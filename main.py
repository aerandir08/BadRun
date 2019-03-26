# -*- coding: utf-8 -*-
import machine
import time
import random
import socket
import ure


def send_response(client, payload, status_code=200):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    client.sendall("Content-Length: {}\r\n".format(len(payload)))
    client.sendall("\r\n")

    if len(payload) > 0:
        client.sendall(payload)


def handle_root(client):
    myform = """<!DOCTYPE html><html>
                    <head>
                        <title>Badminton Training</title>
                        <meta charset="utf-8"/>
                    </head>
                    <body>
                        <h1>Badminton Training</h1>
                        <FONT SIZE=+1>
                        <form method='post' action='start'>
                            Trainingszeit: <input type='number' name='time'><br>
                            Intervall: <input type='number' name='interval'><br>
                            <input type="submit" value="Send"/>
                        </form>
          
                        <FONT SIZE=-2><br>
                        Malte Becker 03/2019<br>
                    </body>
                <html>"""
    send_response(client, myform)


def handle_start(client, request):
    global t, interval
    match = ure.search("time=([^&]*)&interval=(.*)", request)
    t = int(match.group(1).decode("utf-8"))
    print(t)
    interval = int(match.group(2).decode("utf-8"))
    print(interval)

    myform = """<!DOCTYPE html><html>
                        <head>
                            <title>Badminton Training</title>
                            <meta charset="utf-8"/>
                            <style>
                                @keyframes zeigedich{
                                from {opacity:0;height: auto;}
                                to {opacity:1;height: auto;}
                                }
                                
                                @-webkit-keyframes zeigedich{
                                from {opacity:0;height: auto;}
                                to {opacity:1;height: auto;}
                                }
                                #t_button{
                                opacity:0;
                                height: 0;
                                animation-name: zeigedich;
                                animation-duration: 0s;
                                animation-timing-function: linear;
                                animation-fill-mode: forwards;
                                animation-delay: %ds;
                                animation-iteration-count:1;
                                animation-play-state: running;
                                 
                                -webkit-animation-name: zeigedich;
                                -webkit-animation-duration: 0s;
                                -webkit-animation-timing-function: linear;
                                -webkit-animation-fill-mode: forwards;
                                -webkit-animation-delay: %ds;
                                -webkit-animation-iteration-count: 1;
                                -webkit-animation-play-state: running;
                                }
                            </style>
                        </head>
                        <body>
                            <h1>Badminton Training</h1>
                            <FONT SIZE=+1>
                            Training gestartet<br>
                            Laufzeit: %d s
                            <form method='post' action='statistic'>
                                <input type="submit" value="Statistik" id="t_button"/>
                            </form>
                            <FONT SIZE=-2><br>
                            Malte Becker 03/2019<br>
                        </body>
                    <html>""" % (t+5, t+5, t)
    send_response(client, myform)

    # Start Training
    total, speed, speed_av = training(t, interval)
    print(total, speed, speed_av)


def handle_statistic(client, request):
    myform = """<!DOCTYPE html><html>
                            <head>
                                <title>Badminton Training</title>
                                <meta charset="utf-8"/>
                            </head>
                            <body>
                                <h1>Badminton Training</h1>
                                <FONT SIZE=+1>
                                <h3>Statistik</h3>
                                <table>
                                    <tr> <td> Laufzeit: </td> <td> %d s</td></tr>
                                    <tr> <td> Anzahl Läufe: </td> <td> %d</td></tr>
                                    <tr> <td> Durchschnitt: </td> <td> %f s</td></tr>
                                </table>
                                <br>
                                Entwicklung: <br>
                                %s <br><br>
                                <form method='post' action='/'>
                                    <input type="submit" value="Neustart"/>
                                </form>
                                <FONT SIZE=-2><br>
                                Malte Becker 03/2019<br>
                            </body>
                        <html>""" % (t, total, speed_av, speed)
    send_response(client, myform)


def handle_not_found(client, url):
    pass


def get_led():
    return bool(random.getrandbits(1))


# Interrupt function
def end_program(timer):
    print('Timer Interrupt')
    global is_running
    if is_running:
        is_running = False


def training(time_train, interval):
    print('Training gestartet')
    global total, speed, speed_av
    total = 0
    speed = []

    # Short break before start
    led_l.on()
    led_r.on()
    time.sleep(3)
    led_l.off()
    led_r.off()

    timer = machine.Timer(0)
    timer.init(period=time_train * 1000, mode=machine.Timer.ONE_SHOT, callback=end_program)

    while is_running:
        status = get_led()
        start = time.ticks_ms()
        if status:
            led_l.on()
            while not sens_l.value():
                pass
        else:
            led_r.on()
            while not sens_r.value():
                pass
        delta = time.ticks_diff(time.ticks_ms(), start)
        speed.append(delta/1000)
        total = total + 1
        led_l.off()
        led_r.off()
        time.sleep(interval)

    led_l.on()
    led_r.on()
    print('Training beendet')
    speed_av = sum(speed) / len(speed)
    return total, speed, speed_av


print('gestartet')
global led_l, led_r, sens_l, sens_r

# Define LEDs
led_l = machine.Pin(12, machine.Pin.OUT)
led_r = machine.Pin(13, machine.Pin.OUT)

# Define inputs
sens_l = machine.Pin(4, machine.Pin.IN)
sens_r = machine.Pin(5, machine.Pin.IN)

led_l.on()
led_r.on()

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
global server_socket
server_socket = socket.socket()
server_socket.bind(addr)
server_socket.listen(1)

led_l.off()
led_r.off()

while True:
    client, addr = server_socket.accept()
    client.settimeout(5.0)
    request = b""
    try:
        while not "\r\n\r\n" in request:
            request += client.recv(512)
    except OSError:
        pass
    try:
        url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
    except:
        url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
    if url == "":
        is_running = True
        handle_root(client)
    elif url == "start":
        handle_start(client, request)
    elif url == "statistic":
        handle_statistic(client, request)
    else:
        handle_not_found(client, url)
    client.close()
