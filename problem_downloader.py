import imaplib
import email
from email.header import decode_header
import os
import json


def parse_problem_body(txt):
    lines = txt.split('\n')

    problem_body = ''
    questioner = ''
    problem_body_started = False
    for line in lines:
        line = line.strip()
        if line == start_line:
            problem_body_started = True
        elif problem_body_started and line == end_line:
            break
        elif problem_body_started and line.startswith('This problem was asked by'):
            questioner = line.split('This problem was asked by')[1]
        elif problem_body_started:
            problem_body = problem_body + line + '\n'

    return questioner.strip(), problem_body.strip()


def get_problem_body(queried_day):
    subject_str = 'Daily Coding Problem: Problem #' + str(queried_day)
    problem_body = ''
    questioner = ''
    level = ''

    imap = imaplib.IMAP4_SSL(imap_source)

    imap.login(username, password)

    status, messages = imap.select(directory_containing_daily_coding_problem_mails)

    print(messages[0])
    messages = int(messages[0])

    for i in range(messages, 0, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    try:
                        subject = subject.decode()
                    except UnicodeDecodeError:
                        subject = subject.decode('iso-8859-9')
                # email sender
                from_ = msg.get("From")
                if from_ == email_sender:
                    # print("Subject:", subject)
                    # print("From:", from_)
                    if subject.startswith(subject_str):
                        level = subject.split(subject_str)[1]

                        if msg.is_multipart():
                            # iterate over email parts
                            for part in msg.walk():
                                # extract content type of email
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                try:
                                    # get the email body
                                    body = part.get_payload(decode=True).decode()
                                except:
                                    pass
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    # print text/plain emails and skip attachments
                                    questioner, problem_body = parse_problem_body(body)
                                elif "attachment" in content_disposition:
                                    # download attachment
                                    filename = part.get_filename()
                                    if filename:
                                        if not os.path.isdir(subject):
                                            # make a folder for this email (named after the subject)
                                            os.mkdir(subject)
                                        filepath = os.path.join(subject, filename)
                                        # download attachment and save it
                                        open(filepath, "wb").write(part.get_payload(decode=True))
                        else:
                            # extract content type of email
                            content_type = msg.get_content_type()
                            # get the email body
                            body = msg.get_payload(decode=True).decode()
                            if content_type == "text/plain":
                                # print only text email parts
                                questioner, problem_body = parse_problem_body(body)                    
    imap.close()
    imap.logout()

    return questioner, level.strip(), problem_body



def prepare_problem(queried_day):
    if not os.path.isdir(os.path.join(download_directory, 'day_' + str(queried_day))):
        os.makedirs(os.path.join(download_directory, 'day_' + str(queried_day)))
    
    questioner, level, problem_body = get_problem_body(queried_day)

    if questioner == '' and problem_body == '' and questioner == '':
        raise Exception('Daily Coding Problem mail for day ' + str(queried_day) + ' could not be found')

    result = "\"\"\"\n" + level.upper() + "\n\nAsked by " + questioner + "\n\n" + problem_body + "\n\"\"\""

    with open(os.path.join(download_directory, 'day_' + str(queried_day), 'solution.py'), 'w') as f:
        f.write(result)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--configuration')
    parser.add_argument('-d','--day')
    args = parser.parse_args()

    with open(args.configuration) as f:
        data = json.load(f)
        username = data['username']
        password = data['password']
        imap_source = data['imap_source']
        email_sender = data['email_sender']
        directory_containing_daily_coding_problem_mails = data['directory_containing_daily_coding_problem_mails']
        download_directory = data['download_directory']
        start_line = data['start_line']
        end_line = data['end_line']
    
    queried_day = args.day
    prepare_problem(queried_day)
