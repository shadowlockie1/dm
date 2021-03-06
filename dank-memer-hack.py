import json, requests, random, time
from threading import Thread, Semaphore
from queue import Queue
# set these using discord developer mode
from conf import SUPER_PROPS, AUTHORIZATION, USER_AGENT, REFERER, COOKIE, CHANNEL_ID

COMMANDS = [('pls beg', 31), ('pls slots 1', 4), ('pls bet 1', 3), ('pls fish', 31), ('pls pm', 61),
            ('pls trivia', 26), ('pls pet pat', 6), ('pls use candy', 4), ('pls sell fish', 9), ('pls scout', 31),
            ('pls pet feed', 3000), ('pls pet wash', 3000), ('pls pet play', 10000), ('pls rich', 10),
            ('pls dep 1', 60), ('pls with 1', 50), ('pls lottery', 3600)]
WORKERS = len(COMMANDS) + 1
queue = Queue()
nonce_lock, data_lock, secondary_data_lock, request_lock = (
    Semaphore(1), Semaphore(1),
    Semaphore(1), Semaphore(1)
)
channel_url = 'https://discordapp.com/api/v6/channels/{}/messages'.format(str(CHANNEL_ID))
nonce = "722789522290923712" # or some other bignum

data = '{"content":"test","nonce": nonce,"tts":false}'
secondary_data = '{"content":"d","nonce": nonce,"tts":false}'

headers = {
    'authority': 'discordapp.com',
    'x-super-properties': SUPER_PROPS,
    'origin': 'https://discordapp.com',
    'authorization': AUTHORIZATION,
    'accept-language': 'en-US',
    'user-agent': USER_AGENT,
    'content-type': 'application/json',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'referer': REFERER,
    'accept-encoding': 'gzip, deflate, br',
    'cookie': COOKIE,
}


def generate_nonce(nonce): return str(int(nonce) + random.randint(1, 100))


def worker():
    global data, secondary_data, nonce

    while True:
        command, timeout = queue.get()
        time.sleep(timeout)
        dual_command = command in {'pls trivia', 'pls pm', 'pls scout', 'pls lottery'}

        with nonce_lock:
            nonce = generate_nonce(nonce)

        queue.put((command, timeout))

        with data_lock:
            data = json.loads(data)
            data['nonce'] = nonce
            data['content'] = command
            data = json.dumps(data)

        if dual_command:
            with nonce_lock:
                nonce = generate_nonce(nonce)

            with secondary_data_lock:
                secondary_data = json.loads(secondary_data)
                secondary_data['nonce'] = nonce
                if command == 'pls scout':
                    content = 'discord'
                elif command == 'pls lottery':
                    content = 'yes'
                else:
                    content = 'd'
                secondary_data['content'] = content
                secondary_data = json.dumps(secondary_data)

        with request_lock:
            requests.post(channel_url, headers=headers,
                          data=data)
            if dual_command:
                requests.post(channel_url, headers=headers,
                              data=secondary_data)

        queue.task_done()


workers = []
# change timeouts for each command if you're not a normie user
for cmd in COMMANDS:
    queue.put(cmd)
for i in range(WORKERS):
    t = Thread(target=worker)
    t.start()
    workers.append(t)

queue.join()

for i in range(WORKERS):
    queue.put(None)
for t in workers:
    t.join()
