import os
import imaplib, getpass
import re
import email
from bs4 import BeautifulSoup, SoupStrainer
import getopt
import sys
import mechanize
import HTML
import time
import random

def open_connection(username, password, server, verbose=False):
    # Connect to the server
    if verbose: print 'Connecting to ', server
    connection = imaplib.IMAP4_SSL(server)

    # Login to our account
    if verbose: print 'Logging in as', username
    connection.login(username, password)
    return connection

    if __name__ == '__main__':
        c = open_connection(username, password, server, verbose=True)
    try:
        print c
    finally:
        c.logout()

def get_mail_boxes(connection, boxes):
	typ, box_list = connection.list()
	list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

	if typ == "OK":
	   for box in box_list:
            flags, delimiter, mailbox_name = list_response_pattern.match(box).groups()
            mailbox_name = mailbox_name.strip('"')
            boxes.append(mailbox_name)
	   return 1
	return 0

def get_message_ids(connection, mailbox, filter):
    connection.select(mailbox, readonly=False)
    typ, msg_ids = connection.search(None, filter)
    if typ == 'OK':
        return msg_ids[0].split()
    return []

def get_message_text(msg):
    res = ''
    if msg.get_content_maintype() == 'multipart':
        for part in msg.get_payload():
            res = res + get_message_text(part)
    elif msg.get_content_type() == 'text/plain':
        res = res + msg.get_payload()
    return res

def get_message_html(msg):
    res = ''
    if msg.get_content_maintype() == 'multipart':
        for part in msg.get_payload():
            res = res + get_message_html(part)
    elif msg.get_content_type() == 'text/html':
        res = res + msg.get_payload()
    return res

def get_message_date(msg):
    if msg != None:
        return msg['date']
    return ''

def get_message_from(msg):
    if msg != None:
        return msg['from']
    return ''

def get_message_to(msg):
    if msg != None:
        return msg['to']
    return ''

def get_message_subject(msg):
    if msg != None:
        return msg['subject']
    return ''

def get_message_raw(connection, mailbox, id, mark_as_read = False):
    connection.select(mailbox, readonly=False)
    typ, mes_data = connection.fetch(id, '(RFC822)')
    if typ == 'OK':
        for response_part in mes_data:
            if isinstance(response_part, tuple):
                if mark_as_read == True:
                    connection.store(id, '+FLAGS', '\\Seen')
                return email.message_from_string(response_part[1])
    return None
            
def main(argv):
    username = ''
    server = ''
    post_links = dict()
    mail_messages = dict()
    output_file = 'articles.html'
    mailbox = 'Inbox'
    mails_to_process = -1
    try:
        opts, args = getopt.getopt(argv,"hu:s:l:f:n:",["username=", "server=", "output_file=", "mails_to_process="])
    except getopt.GetoptError:
        print __file__ , '-u <username> -s <mail server> -f <output file> -n <mails to process>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print __file__ ,'-u <username> -s <mail server> -f <output file> -n <mails to process>'
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-s", "--server"):
            server = arg
        elif opt in ("-f", "--output_file"):
            output_file = arg
        elif opt in ("-n", "--mails_to_process"):
            mails_to_process = int(arg)
    if username == '' or server == '':
        print __file__ , '-u <username> -s <mail server> -f <output file> -n <mails to process>'
        sys.exit(2)

    print 'Username is ', username
    print 'Mail server is ', server
    print 'LinkedIn accound is ', username + '@gmail.com'

    mailcon = open_connection(username, getpass.getpass('Get password for user %s: ' % username), server)
    ids = get_message_ids(mailcon, mailbox, '(UNSEEN FROM "group-digests@linkedin.com")')
    mail_counter = 1
    sum_of_all_links = 0

    browser = mechanize.Browser()
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0')]

    browser.open('https://www.linkedin.com/uas/login?goback=&trk=hb_signin')
    browser.select_form(name='login')
    browser['session_key'] = username + '@gmail.com' #TODO chage the default server to the dynamic one
    browser['session_password'] = getpass.getpass('Get LinkedIn password: ')
    browser.submit()
    browser.response().read()

    linksToArticle = SoupStrainer('h4', attrs={'class' : 'article-title'})
    table_data = HTML.Table(header_row=['Publish Date',   'Article', 'Source'])
    resp = ''

    if mails_to_process < 0:
        mails_to_process = len(ids)
    print "Mails to process: ", mails_to_process, "out of", len(ids)

    for id in ids:
        if mail_counter > mails_to_process:
            print "Processing is done."
            break

        raw_msg = get_message_raw(mailcon, mailbox, id, True)
        if raw_msg != None:
            print 'Processing message from %s' % get_message_from(raw_msg), ".Mails done:", mail_counter , "/", mails_to_process
            html_message = get_message_html(raw_msg)
            soup = BeautifulSoup(html_message, "lxml")
            for job in soup.findAll(lambda tag: tag.name == 'div' and len(tag.contents) > 0 and 'Job' in tag.contents[0]):
                job.parent.extract()

            for line in soup.findAll(lambda tag: tag.name == 'a' and len(tag.findAll('strong')) == 1):
                try:
                    browser.open(line['href'])
                    resp = browser.response().read()
                except (mechanize.HTTPError, mechanize.URLError) as e:
                    continue

                h4Tag = BeautifulSoup(resp, "lxml", parse_only=linksToArticle)
                aTag = h4Tag.find('a')
                spanTag = h4Tag.find('span')
                if aTag != None and spanTag != None and len(spanTag.contents) > 0  and aTag.attrs['data-contentpermalink'] != None and line.strong.string != None and not aTag['data-contentpermalink'] in post_links:
                    post_links[aTag['data-contentpermalink']] = line.strong.string
                    date = time.strftime("%a, %d %b %Y", time.strptime(get_message_date(raw_msg), '%a, %d %b %Y %H:%M:%S +0000 (%Z)'))
                    article_link = '<a href=' + aTag['data-contentpermalink'] + '>' + line.strong.string + '</a>'
                    article_src = spanTag.contents[0]
                    table_data.rows.append([date , article_link, article_src])
                sum_of_all_links = sum_of_all_links + 1
                time.sleep(random.randint(1, 10))
            mail_counter = mail_counter + 1

        if mail_counter % 50 == 0:
            f = open(output_file + '.bak', 'w')
            f.write(unicode(table_data).encode('utf-8'))
            f.close()

    mailcon.logout()
    print "Unique links in the mails: ", len(post_links)
    print "Sum of all links in the mails: ", sum_of_all_links
    f = open(output_file, 'w')
    f.write(unicode(table_data).encode('utf-8'))
    f.close()
    if os.path.isfile(output_file + '.bak'):
        os.remove(output_file + '.bak')

if __name__ == "__main__":
   main(sys.argv[1:])
