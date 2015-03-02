#!/usr/bin/env python
######################################################################
#
#	Module		jmlm.py (Jeff's Mailing List Manager)
#	Version		v1.3.1
#	Author		Jeffrey Clement <jclement@bluesine.com>
#	Patches:	Stefano Balocco <stefano.balocco@gmail.com>
#	Targets		Win32, Unix
#	Web		https://github.com/StefanoBalocco/jmlm.py
#
# A quick and dirty little mailing list package intended to be run
# by someone who doesn't have a dedicated mail server.	Can easily 
# run through an existing POP / SMTP mail account with your ISP for
# example.
#
# This is not an appropriate way to run a high traffic list but if 
# you just want a small low traffic list and don't want to pay for it
# you can use jmlm and a dedicated POP3 account for it.
#
# -------------------------------------------------------------------
#
# Revision 1.3.1	2015/03/02		stefano
# Changed indentation, removed subversion crap
# Added SMTP starttls and authentication
#
# Revision 1.3		2003/09/12 20:27:55	jsc
# Bug fixes
#
# Revision 1.2		2003/09/12 19:58:04	jsc
# Mostly all working.  Now just need to bug fix.
#
# Revision 1.1.1.1	2003/09/11 21:04:43	jsc
# Project Created
#
# -------------------------------------------------------------------
#
# Copyright (c) 2003, Jeffrey Clement All rights reserved. 
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met: 
#
# * Redistributions of source code must retain the above copyright notice, 
#	this list of conditions and the following disclaimer. 
# * Redistributions in binary form must reproduce the above copyright 
#	notice, this list of conditions and the following disclaimer in the 
#	documentation and/or other materials provided with the distribution. 
# * Neither the name of the Bluesine nor the names of its contributors 
#	may be used to endorse or promote products derived from this software 
#	without specific prior written permission. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

# SMTP & POP3 credential
MAIL_USER		= 'list@jclement.ca'
MAIL_PASS		= 'a'

# SMTP Server for outgoing mail.  This server must relay messages to
# all subscribed addresses
SMTP_SERVER		= 'mail.bluesine.com'
SMTP_REQUIRE_AUTH	= False
SMTP_REQUIRE_TLS	= False

# POP3 Server for the list
POP3_SERVER = 'mail.bluesine.com'

# List Name - reported in subject of list messages
LIST_NAME	= 'JMLM-TEST'

# The From address for messages sent by the listserv.  Also the Reply to 
# address if enabled.
LIST_ADDR	= 'list@jclement.ca'

# Owner address (probably your personal mail)
LIST_OWNER	= 'jclement@jclement.ca'

# File containing list of users subscribed to the list
SUB_LIST	= 'users'

# Key used for generating e-mail hashes for server responses
LIST_KEY  = ')(80OIJSLKRJLJD)(823lkjF'

# Only subscribers may post?
SUB_POST	= True	  

# Force the reply-to header to be list address?
REPLYTO_LIST= True

# Maximum message size in bytes
MAX_SIZE	= 50000

# Send to self
SEND_TO_SELF= True

##########################################################################

MSG_SUBSCRIBE = '''Hello,  

This is the list server for (%(list_name)s).  We recieved a subscription
request for the following e-mail address on %(time)s.

  %(from_addr)s

If this request was initiated by you just reply to this message, making 
sure not to alter the subject line (Adding Re: in front is fine).  

If you did not initiate this request just ignore this message.	No 
further action is needed.  You will not be subscribed unless you reply to 
this message.

Thank you

%(original)s
'''

MSG_ALREADY_SUBSCRIBED = '''Hello,

This is the list server for (%(list_name)s).  We recieved a subscription
request for the following e-mail address on %(time)s.

  %(from_addr)s

It seems this address is already subscribed to this mailing list.  

Thank you

%(original)s
'''

MSG_WELCOME = '''Hello,

Welcome to the mailing list.  

To post messages to the list simple send them your messages to:

  %(list_addr)s
  
If you wish to unsubscribe from this mailing list simple send a message
to %(list_addr)s with the subject "Unsubscribe" without the double quotes.

Thank you

%(original)s
'''

MSG_UNSUBSCRIBE = '''Hello,

This is the list server for (%(list_name)s).  We recieved an unsubscribe
request for the following e-mail address on %(time)s.

  %(from_addr)s

If this request was initiated by you just reply to this message, making 
sure not to alter the subject line (Adding Re: in front is fine).  

If you did not initiate this request just ignore this message.	No 
further action is needed.  You will not be unsubscribed unless you reply to 
this message.

Thank you

%(original)s
'''

MSG_NOT_SUBSCRIBED = '''Sorry,

Your request to unsubscribe from this list has failed because you
are not subscribed to this mailing list with this address:

   %(from_addr)s

If you are receiving messages from this list it is possible you are
subscribed with another e-mail address.	 Look at the headers of the 
messages and send the unsubscribe request from that address.

Thank you

%(original)s
'''

MSG_GOODBYE = '''Thank you,

Your request to unsubscribe from this list has been processed.

Good bye

%(original)s
'''

MSG_OVERSIZE = '''Sorry,

The message that follows was rejected by this mailing list for the
following reason:

  Message exceeds size limit of %(max_size)s bytes.

If you feel you have a legitimate reason for posting a message of
this size please contact the list owner at:
 
  %(list_owner)s

Thank you,

%(original)s
'''

MSG_ONLY_SUBSCRIBERS_MAY_POST = '''Hello,

This is the list server for (%(list_name)s).  Unfortunately the following
message could not be posted to this mailing list as this list only allows
posts by subscribers.  

If you would like to subscribe to this mailing list please send an empty
e-mail message to %(list_addr)s with the subject "Subscribe" without the 
double quotes.

Thank you

%(original)s
'''


##########################################################################

import os
import re
import sys
import md5
import time
import email
import rfc822
import dbhash
import string
import poplib
import getopt
import smtplib
import email.Utils
import email.Message
from StringIO import StringIO

# SMTP

def sendMessage(to, message):
	server = smtplib.SMTP(SMTP_SERVER)
	server.ehlo()
	if SMTP_REQUIRE_TLS:
		server.starttls()
		server.ehlo()
	if SMTP_REQUIRE_AUTH:
		server.login(MAIL_USER,MAIL_PASS)
	server.sendmail(LIST_ADDR, to, message)
	
def sendDaemonMessage(to, subject, message, prev_message=None):
	"""
	Send a message to user from the list-serv.	If prev_message is 
	provided it is quoted in the message.  

	NOTE: prev_message is supposed to be a list on lines in the message
	as provided by the POP client
	"""
	header = 'Date: %s\r\nFrom: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n' % (
		email.Utils.formatdate(),
		LIST_ADDR,
		to,
		'[%s] %s' % (LIST_NAME, subject))
	if prev_message:
		message += "\r\n\r\n"
		message += '\r\n'.join(map(lambda s: ' > %s' % s, prev_message))
	sendMessage(to, header+message)

##########################################################################

def usage():
	print "*"*78
	print "jmlm.py - Jeff's Mailing List Manager"
	print ""
	print "Copyright (C) 2003 Jeffrey Clement"
	print "This is free software; see the source for copying conditions.  There is NO"
	print "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."
	print ""
	print "usage: jmlm.py <options>"
	print "	 -h		this help screen"
	print "	 -p		process mailing list traffic"
	print "	 -l		list subscribed users"
	print "	 -s <email>	subscribe user"
	print "	 -u <email>	unsubscribe user"
	print ""
	print "*"*78

def err(m):
	print "ERROR: ",m
	sys.exit(0)

##########################################################################

def validEmail(emailAddr):
	pattern = re.compile('^([_a-zA-Z0-9-+]\.*){1,255}@([_a-zA-Z0-9-]\.*){1,255}\.([a-zA-Z]){2,3}$')
	return pattern.match(emailAddr) != None

##########################################################################

def key(from_addr, op):
	return '['+md5.md5('%s -- %s -- %s' % (from_addr.lower(), op.lower(), LIST_KEY)).hexdigest()[:8]+']'

def processMessage(rawmsg):

	message = email.message_from_string('\r\n'.join(rawmsg))
	from_addr = email.Utils.parseaddr(message.get('from',''))[1]
	subject = message.get('subject','')

	fields = {}
	fields['subject'] = subject
	fields['from_addr'] = from_addr
	fields['list_name'] = LIST_NAME
	fields['original'] = '\r\n'.join(map(lambda s: ' > %s' % s, rawmsg))
	fields['time'] = time.ctime()
	fields['max_size'] = MAX_SIZE
	fields['list_owner'] = LIST_OWNER
	fields['list_addr'] = LIST_ADDR

	# drop any messages with invalid from addresses
	if not validEmail(from_addr):
		print "dropped(ivfr)",
		return
	
	# drop any messages from the list
	if from_addr == LIST_ADDR.lower():
		print "dropped(frlst)",
		return

	# drop any bounced messages (ie. <> return path)
	if message.get('return-path','<>') == '<>':
		print "dropped(nrp)",
		return

	# drop any messages with myself in Recieved headers
	#for header in message.get_all('Receieved'):
	#	 if header.find(LIST_ADDR) != -1:
	#		 print "dropped(rcv)",
	#		 return

	# drop any messages where priority = mailing list
	if message.get('precedence','').lower() in ['bulk','list']:
		print "dropped(bulk)",
		return

	# process admin commands
	if subject.find(key(from_addr,'subscribe')) != -1:
		if USERS.has_key(from_addr):
			s = 'Already subscribed'
			m = MSG_ALREADY_SUBSCRIBED % fields
			print "sub(already)",
		else:
			USERS[from_addr]=from_addr
			s = 'Welcome to the list'
			m = MSG_WELCOME % fields
			print "sub(comp)",
		sendDaemonMessage(from_addr, s, m)	  
		return
	if subject.strip().lower() == 'subscribe' != -1:
		if USERS.has_key(from_addr):
			s = 'Already subscribed'
			m = MSG_ALREADY_SUBSCRIBED % fields
			print "sub(already)",
		else:
			s = 'Subscription Confirmation %s' % key(from_addr, 'subscribe')
			m = MSG_SUBSCRIBE % fields
			print "sub(conf)",
		sendDaemonMessage(from_addr, s, m)	  
		return
	if subject.find(key(from_addr,'unsubscribe')) != -1:
		if USERS.has_key(from_addr):
			del USERS[from_addr]
			s = 'Unsubscribe successful'
			m = MSG_GOODBYE % fields
			print 'unsub(comp)',
		else:
			s = 'Not subscribed'
			m = MSG_NOT_SUBSCRIBED % fields
			print "unsub(notsub)",
		sendDaemonMessage(from_addr, s, m)	  
		return
	if subject.strip().lower() == 'unsubscribe':
		if USERS.has_key(from_addr):
			s = 'Unsubscription Confirmation %s' % key(from_addr, 'unsubscribe')
			m = MSG_UNSUBSCRIBE % fields
			print "unsub(conf)",
		else:
			s = 'Not subscribed'
			m = MSG_NOT_SUBSCRIBED % fields
			print "unsub(notsub)",
		sendDaemonMessage(from_addr, s, m)	  
		return
	
	# bounce messages over given size
	if len('\r\n'.join(rawmsg)) > MAX_SIZE:
		s = 'Message over size limit'
		m = MSG_OVERSIZE % fields
		sendDaemonMessage(from_addr, s, m)
		print "bounced(size)",
		return

	# if subsriber only post is enabled bounce message from those
	# not on the list.
	if SUB_POST and not USERS.has_key(from_addr):
		s = 'Only subscribers may post'
		m = MSG_ONLY_SUBSCRIBERS_MAY_POST % fields
		sendDaemonMessage(from_addr, s, m)
		print "bounced(nonsub)",
		return

	# find where end of headers

	# strip out the various headers we don't want
	# like return path, precendence, etc.
	for header in ['return-path','delivered-to','precedence','reply-to']:
		if message.has_key(header): del message[header]

	# Add self to Received
	message.add_header('Received','from %s at %s' % (LIST_NAME, LIST_ADDR))

	# tweak things like subject, etc
	if not message.has_key('subject'):
		message['subject'] = ''
	if message['subject'].find('[%s]' % LIST_NAME) == -1:
		message.replace_header('subject','[%s] %s' % (LIST_NAME, message['subject']))

	# insert Priority header
	message.add_header('Precedence','list')

	# reply to list?
	if REPLYTO_LIST:
		message.add_header('Reply-to',
			email.Utils.formataddr((LIST_NAME, LIST_ADDR)))

	# resend message to all recipients
	for recipient in USERS.keys():
		if (recipient != from_addr or 
			(recipient == from_addr and SEND_TO_SELF)):
			sendMessage(recipient, message.as_string())
	print "delivered",
	

##########################################################################

def processMailinglist():

	print "JMLM:  Processing Mailing List"

	# log into the POP3 server
	popserver = poplib.POP3(POP3_SERVER)
	try:
		assert(popserver.user(MAIL_USER) == '+OK ')
		assert(popserver.pass_(MAIL_PASS) == '+OK ')
	except:
		err("Unable ot login to POP3 server.  Please verify username and password")
	print " - connected to POP3 server"

	# get message list
	res, list, sz = popserver.list()
	if (res != '+OK '): err('Unable to retrieve message list from server')
	print " - %d messages in queue" % len(list)

	# loop through messages
	for tmp in list:
		id,size = map(int, tmp.split(' '))
		print "	  - processing message %d (%d bytes):" % (id, size),
		ret, msg, other = popserver.retr(id)
		if ret[:3] != '+OK': err('Unable to retrieve message')
		print "downloaded",
		processMessage(msg)
		print "del",
		popserver.dele(id)
		print "done"

	# signof and commit
	popserver.quit()
		
##########################################################################

USERS = dbhash.open(SUB_LIST,'c',0)
#	 err('Unable to open subscribers list.	Unable to continue!')

if __name__=='__main__':
	opts, args = getopt.getopt(sys.argv[1:], 'hpls:u:')
	for k,v in opts:
		if k == '-p':
			processMailinglist()
			sys.exit(0)
		if k == '-l':
			lst = USERS.keys()
			lst.sort()
			for u in lst:
				print u
			sys.exit(0)
		if k == '-s':
			if not USERS.has_key(v):
				USERS[v]=v
			sys.exit(0)
		if k == '-u':
			if USERS.has_key(v):
				del USERS[v]
			sys.exit(0)
	usage()
