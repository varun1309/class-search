from selenium import webdriver
import time
from twilio.rest import Client
from threading import Thread
import smtplib
from flask import Flask, request


app = Flask(__name__)

class_list_dictionary = dict()
started = 0

@app.route("/")
def home():
    return """
    <h1>Welcome to ASU Class Search Application!!!</h1>
    <h2>Just add the courses you want to search and receive SMS notification when they are open. Right now its
    only designed for me. </h2>
    <form action="start" method="POST">
        <input type="input" name="course" placeholder="Course, example - cse"/><br/>
        <input type="input" name="number" placeholder="Number, example - 575"/><br/>
        <input type="input" name="phone" placeholder="email"/><br/>
        <input type="submit"/>
    </form>
    """


@app.route("/start", methods=['POST'])
def start():
    course = request.form['course']
    number = request.form['number']
    phone = request.form['phone']

    # Validating if the form values are correct.
    if course == "" or number == "" or phone == "":
        return """
           <h2><strong>Bad form values. Go back.</strong></h2> 
           """

    global started
    global class_list_dictionary
    class_list_dictionary[course+'-'+number] = 0

    thread1 = Thread(target=search_class, args=(phone, course+'-'+number,))
    thread1.start()

    return """
        <h1>Process started in a new thread</h1>
        <a href="/">Home</a>
        
        """


def search_class(phone, course_details):
    try:
        account_sid = "twilio sid"
        auth_token = "twiliio token"
        client = Client(account_sid, auth_token)

        courseTitle = course_details.split('-', 2)[0]
        courseNumber = course_details.split('-', 2)[1]

        url_page = "https://webapp4.asu.edu/catalog/classlist?t=2187&s=" + courseTitle + "&n=" + courseNumber + "&l=grad&hon=F&promod=F&e=all&page=1"
        driver = webdriver.PhantomJS('bin/phantomjs')
        driver.get(url_page)
        driver.set_window_size(1400, 1000)

        avail = '0'
        while avail == '0':

            try:
                time.sleep(5)
                avail = driver.find_element_by_xpath("//div[@class='col-xs-3'][1]").text

            except Exception as e:
                print('Unable to find element. Will try again in a while - ', course_details, " ->", e.__str__())
                print("refreshing the page")
                driver.refresh()
                time.sleep(2)
                continue

            email_to_send = sms_to_send = 'Seats found in ' + courseTitle + ' ' + courseNumber + '= ' + avail
            print(email_to_send)

            if avail == '0':
                time.sleep(60)
            else:
                print("Found open seats. Sending sms", course_details, "->", phone)
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login("your@gmail.com", "pw")
                server.sendmail("your@gmail.com", phone, sms_to_send)
                server.quit()

                message = client.messages.create(body=sms_to_send,
                                                 to="+target",  # Replace with your phone number
                                                 from_="+twilio number")  # Replace with your Twilio number
                driver.close()
                print(message.sid)

    except Exception as e:
        print("Caught some exception. Calling self again ->", phone, e.__str__())
        driver.close()
        del driver
        search_class(phone, course_details)


if __name__ == '__main__':
    app.run()
