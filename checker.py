# -*- coding: utf-8 -*-
__author__ = 'alexey'
from themis.checker import Server, Result
import string, random, os
import requests
import tempfile

class SequencerChecker(Server):

    functions = ["count-nucleo", "dna-to-rna", "reverse-complement-dna"]

    def create_task_string(self,flag):
        task = ""
        task+="name;"+self.genlogin()+"\n"
        task+="func;"+random.choice(self.functions)+"\n"
        data = ''.join(random.choice(['A', 'C', "T", "G"]) for i in range(random.randint(5,15)))
        task+="data;"+"{"+":s1 "+data+"}"+"\n"
        task+="comment;"+flag+"\n"
        return task

    def create_temp_task_file(self,flag):
        fd, filename = tempfile.mkstemp("sequencer",text=True)
        os.write(fd, self.create_task_string(flag))
        os.close(fd)
        return fd, filename

    def genpassword(self):
        length = random.randint(10, 15)
        chars = string.ascii_letters + string.digits + '_'
        random.seed = (os.urandom(1024))
        return ''.join(random.choice(chars) for i in range(length))

    def genlogin(self):
        length = random.randint(5,12)
        chars = string.ascii_letters+string.digits+'_'
        random.seed = (os.urandom(1024))
        return ''.join(random.choice(chars) for i in range(length))

    def push(self, endpoint, flag_id, flag):
        username = self.genlogin()
        password = self.genpassword()
        payload = {'username':username, 'password':password}
        try:
            r = requests.post("http://"+endpoint+":8080/do-register", data=payload, timeout=10)
            if r.status_code == 200:
                try:
                    fd, filename = checker.create_temp_task_file(flag)
                    cookie = r.history[0].cookies["JSESSIONID"]
                    print username
                    print password 
		    files = {'task': open(filename,"r")}
                    r2 = requests.post("http://"+endpoint+":8080/",files=files, cookies=dict(JSESSIONID=cookie), timeout=10)
                    if r2.status_code == 200:
                        text = r2.text
                        if not flag in text:
                            return Result.CORRUPT, username+";"+password
                        else:
                            return Result.UP, username+";"+password
                    else:
                        return Result.MUMBLE, username+";"+password
                finally:
                    os.remove(filename)
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
           payload = {'username':username, 'password':password}
           r = requests.post("http://"+endpoint+":8080/do-login", data=payload, timeout=10)
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
