# -*- coding: utf-8 -*-
__author__ = 'alexey'
from themis.checker import Server, Result
import string, random, os
import requests
import tempfile
import collections

seq_dict = {'A':'T', "T":"A", "G":"C", "C":"G"}

class SequencerChecker(Server):
    functions = ["count-nucleo", "dna-to-rna", "reverse-complement-dna"]

    def solve(self, data_string, task):
        if task == "count-nucleo":
            count = collections.Counter(data_string)
            if count.get("A",0) != 0:
                return "A:"+str(count.get("A"))
            elif count.get("T",0) !=0:
                return "T:"+str(count.get("T"))
            elif count.get("C",0) !=0:
                return "C:"+str(count.get("C"))
            else:
                return "G:"+str(count.get("G"))
        elif task == "dna-to-rna":
            return data_string.replace("T","U")
        elif task == "reverse-complement-dna":
            return "".join(seq_dict[base] for base in reversed(data_string))

    def create_task_string(self, flag):
        task = ""
        task += "name;" + self.gen_login() + "\n"
        func = random.choice(self.functions)
        task += "func;" + func + "\n"
        data = ''.join(random.choice(['A', 'C', "T", "G"]) for i in range(random.randint(8, 25)))
        task += "data;" + "{" + ":s1 " + data + "}" + "\n"
        task += "comment;" + flag + "\n"
        res = self.solve(data,func)
        return task, res

    def create_temp_task_file(self, flag):
        fd, filename = tempfile.mkstemp("sequencer", text=True)
        data, res = self.create_task_string(flag)
        os.write(fd, data)
        os.close(fd)
        return fd, filename, res

    @staticmethod
    def gen_password():
        length = random.randint(10, 15)
        chars = string.ascii_letters + string.digits + '_'
        random.seed = (os.urandom(1024))
        return ''.join(random.choice(chars) for i in range(length))

    @staticmethod
    def gen_login():
        length = random.randint(5, 12)
        chars = string.ascii_letters + string.digits + '_'
        random.seed = (os.urandom(1024))
        return ''.join(random.choice(chars) for i in range(length))

    def push(self, endpoint, flag_id, flag):
        username = self.gen_login()
        password = self.gen_password()
        payload = {'username': username, 'password': password}
        try:
            r = requests.post("http://" + endpoint + ":8080/do-register", data=payload, timeout=10)
            if r.status_code == 200:
                try:
                    fd, filename, res = checker.create_temp_task_file(flag)

                    cookie = r.history[0].cookies["JSESSIONID"]
                    print username
                    print password
                    print res
                    files = {'task': open(filename, "r")}
                    r2 = requests.post("http://" + endpoint + ":8080/", files=files, cookies=dict(JSESSIONID=cookie),
                                       timeout=10)
                    if r2.status_code == 200:
                        text = r2.text
                        if not res in text:
                            return Result.CORRUPT, username + ";" + password
                        else:
                            if not flag in text:
                                return Result.CORRUPT, username + ";" + password
                            else:
                                return Result.UP, username + ";" + password
                    else:
                        return Result.MUMBLE, username + ";" + password
                finally:
                    try:
                        os.remove(filename)
                    except WindowsError:
                        pass
            else:
                return Result.MUMBLE, ""
        except requests.ConnectionError:
            return Result.DOWN, ""
        except requests.HTTPError:
            return Result.DOWN, ""
        except requests.exceptions.Timeout:
            return Result.DOWN, ""

    def pull(self, endpoint, flag_id, flag):
        username, password = flag_id.split(';')
        try:
            payload = {'username': username, 'password': password}
            r = requests.post("http://" + endpoint + ":8080/do-login", data=payload, timeout=10)
            if r.status_code == 200:
                text = r.text
                if not flag in text:
                    return Result.CORRUPT
                else:
                    return Result.UP
            else:
                return Result.MUMBLE
        except requests.ConnectionError:
            return Result.DOWN
        except requests.HTTPError:
            return Result.DOWN
        except requests.exceptions.Timeout:
            return Result.DOWN


checker = SequencerChecker()
checker.run()
