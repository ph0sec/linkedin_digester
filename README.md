LinkedIn Digester
=================

The digester is a tool to process digests sent to your mail as the result of your subscription to various LinkedIn discussion groups. It will connect to your mail box and extract all the relevant mails and process them to generate a HTML file with the table of links to the target articles that were posted on the particular discussion group:

| Article publish date  | Article Link | Source      |
| :-----: 				 | :-----: 		| :-------:   |
| Date					 | The article  | Some source |

The mails itself will remain and will be marked as read. In addition, the script will do accessional backup of processed results and of course clean after itself when done.

### Usage:

linkedin_digester.py

	-u <email username>			- the user name of your mail account
	-s <mail server>			- the mail server
	-f [output file] 			- output file, optional
	-n [mails to process]		- mails to process, optional.
	
	
### Example:

**linkedin_digester.py** **-u** your_name **-s** imap.gmail.com **-f** digests.html **-n** 200


### Dependencies:

- [Mechanize](http://wwwsearch.sourceforge.net/mechanize/)
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/)
- [lxml](http://lxml.de/)
- [HTML.py](http://www.decalage.info/python/html) with some customizations (supplied)


### Known Issues:

- The script assumes that the supplied mail is the same one to use for login to LinkedIn account
- Only *gmail.com* support as the appendix that would be added to the supplied mail box username
