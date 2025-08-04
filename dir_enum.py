#!/usr/bin/env python3
import requests
import argparse
import sys
import os
import subprocess
import time
import threading
import queue
from logo import logo
from termcolor import colored

error_counter = 0
counter = 0
lock = threading.Lock()
time_count = 0
stop_event = threading.Event()

def time_thread():
    global time_count
    while not stop_event.is_set():
        time.sleep(1)
        time_count += 1

def brute_force_worker(host, q, q_size):
    global counter, time_count, error_counter
    while not stop_event.is_set():
        try:
            word = q.get(timeout=1)
            url = f"{host}/{word}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    with lock:
                        print(colored(f"\n[+] URL Found : {url}", 'green') + " -->> " + colored(f"Status Code : {response.status_code}", 'magenta'))

            except requests.exceptions.RequestException as e:
                with lock:
                    error_counter += 1
        except queue.Empty:
            break
        finally:
            with lock:
                counter += 1
            if not stop_event.is_set():
                progress = (counter / q_size) * 100
                print(colored(f"\r[*] Progress: {counter}/{q_size} ({progress:.2f}%) - Elapsed Time: {time_count}s - Errors : {error_counter}", 'yellow'), end='', flush=True)
                q.task_done()

def main():
    """Main function to parse the arguments and run the script"""
    subprocess.run(["clear"])
    print(colored(logo, 'blue'))
    print("\tA simple, multi-threaded web directory and file fuzzer.\n\n")
    parser = argparse.ArgumentParser(
        description=colored("A simple, multi-threaded web directory and file fuzzer.", 'cyan'),
        epilog=colored(f"Example: python {sys.argv[0]} http://example.com -w /path/to/wordlist.txt -t 10", 'cyan')
    )
    parser.add_argument("host", help="The target IP address or hostname (e.g., http://example.com).")
    parser.add_argument("-w", "--word-list", required=True, help="Path to the wordlist file.")
    parser.add_argument("-x", "--extension", nargs="+", help="File extensions to test (e.g., php html js).")
    parser.add_argument("-t", "--thread", type=int, default=10, help="Number of threads to use (default: 10).")

    args = parser.parse_args()
    worker_queue = queue.Queue()

    try:
        with open(args.word_list, 'r') as dir_list:
            for dir_word in dir_list:
                dir_word = dir_word.strip()
                worker_queue.put(dir_word)
                if args.extension:
                    for ex in args.extension:
                        file_word = f"{dir_word}.{ex}"
                        worker_queue.put(file_word)
    except FileNotFoundError:
        print(colored("[!] Error!, The File Not Found . Exiting ...\n", 'red'))
        sys.exit(1)

    q_size = worker_queue.qsize()

    threads = []
    for _ in range(args.thread):
        t = threading.Thread(target=brute_force_worker, args=(args.host, worker_queue, q_size,))
        t.start()
        threads.append(t)
    
    time_th = threading.Thread(target=time_thread)
    time_th.start()
    
    try:
        worker_queue.join()
    except KeyboardInterrupt:
        print(colored("\n[!] Keyboard interrupt received. Stopping all threads...\n", 'red'))

    stop_event.set()
    
    for t in threads:
        t.join()


    time_th.join()

    print(colored("\n[*] Fuzzing finished.\n", 'green'))

    

if __name__ == "__main__":
    try:
        main()
    except:
        pass
