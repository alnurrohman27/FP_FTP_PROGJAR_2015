import select
import socket
import sys
import threading
import os

#Class untuk Server
class Server:
    #spesifikasi dari socket ftp server
    def __init__(self):
        self.host = 'localhost'
        self.port = 2728
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []

    #inisialisasi socket ftp server    
    def open_socket(self):        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host,self.port))
        self.server.listen(5)
        print 'Server FTP Siap'
        
    #menu yang akan dijalankan pertama kali saat server dimulai
    def run(self):
        self.open_socket()
        #input = [self.server, sys.stdin]
        input = [self.server]
        #running = 1
        while True:
            #select untuk socket
            inputready,outputready,exceptready = select.select(input,[],[])
            for s in inputready:
                if s == self.server:
                    # handle the server socket - menjalankan client dengan multithreading
                    #self.client_socket, self.client_address = self.server.accept()
                    #self.input.append(self.client_socket)
                    c = Client((self.server.accept()))
                    c.start()
                    self.threads.append(c)
                elif s == sys.stdin:
                    # handle standard input
                    junk = sys.stdin.readline()
                    break

        # close all threads
        self.server.close()
        for c in self.threads:
            c.join()

#Class untuk Client
class Client(threading.Thread):
    #Spesifikasi untuk socket client yang berhasil terhubung
    def __init__(self,(client,address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 4096
        self.wm = 1
        self.id_exit = True
        self.base = os.path.join(os.getcwd(), 'shared folder')
        self.cwd = '/'
        self.fullpath = self.base
        self.pasv_status = False

    #menu yang akan jalan pertama kali saat client berhasil terhubung    
    def run(self):
        if self.wm:
            self.welcome_message()
            self.wm = 1
        self.cek_user()
        
        
    def welcome_message(self):
        self.welcome_msg = '220-FTP Server Versi 1.0\r\nRespon: 220-Ditulis oleh Kelompok XXX\r\n'
        print 'Respon: ' + self.welcome_msg.strip(), self.client.getpeername()
        self.client.send(self.welcome_msg)
    #menu untuk pengecekan user           
    def cek_user(self):
        self.command = self.client.recv(self.size)
        print 'Perintah: ' + self.command.strip(), self.client.getpeername()
        if 'USER Adian\r\n' in self.command:
            self.nama_user = self.command.split(' ')
            self.login_msg = '331 Silahkan masukan password untuk ' + self.nama_user[1] + '\r\n'
            print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()
            self.client.send(self.login_msg)

            self.command = self.client.recv(self.size)

            if self.command == 'PASS 1234\r\n':
                self.login_msg = '230 Anda masuk\r\n'
                self.client.send(self.login_msg)
                print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()

                self.menu_log_in()
                              
            else:
                self.login_msg = 'Username atau password salah\r\n'
                self.client.send(self.login_msg)
                print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()
                self.cek_user()
                #print 'E'
                            
        else:
            self.message = '500 Perintah tidak diketahui\r\n'
            self.login_msg = '530 Silahkan masuk terlebih dahulu'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()
            self.client.sendall(self.message + self.login_msg)
            self.cek_user()

    #menu untuk masuk ke mode pasif    
    def passive_mode(self):
        self.command = self.client.recv(self.size)
        print 'Perintah: ' + self.command.strip(), self.client.getpeername()

        if 'TYPE' in self.command:
            self.code_type = self.command.split(' ')[-1].split('\r\n')
            self.message = '220 TYPE diubah ke ', self.code_type
            self.message += '\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            self.passive_mode()

        elif self.command == 'QUIT\r\n':
            self.login_msg = '221 Anda keluar\r\n'
            self.client.send(self.login_msg)
            print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()
            self.stop()
        elif 'HELP' in self.command:
            self.helps()
        else:
            if 'CWD' in self.command:
                self.cwd_func()
            elif 'PWD' in self.command:
                self.pwd()
            elif 'STOR' in self.command:
                self.stor()
            elif 'RETR' in self.command:
                self.retr()
            elif 'RNFR' in self.command:
                self.rnfr()
            elif 'MKD' in self.command:
                self.mkd()
            elif 'RMD' in self.command:
                self.rmd()
            elif 'DELE' in self.command:
                self.dele()
            elif 'LIST' in self.command:
                self.LIST()
            else:
                self.message = '500 Perintah tidak diketahui\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
                self.passive_mode()

    #menu untuk user yang apabila telah berhasil login
    def menu_log_in(self):
        self.command = self.client.recv(self.size)
        print 'Perintah: ' + self.command.strip(), self.client.getpeername()

        if self.command == 'PASV\r\n':
            self.message = '227 Masuk ke mode pasif\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            ftp_data = ('localhost', 42728)
            self.server_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_data.bind(ftp_data)
            self.server_data.listen(1)
            self.client_data, self.client_data_address = self.server_data.accept()
            self.pasv_status = True
            
            self.passive_mode()
                                                                                            
        elif self.command == 'QUIT\r\n':
            self.login_msg = '221 Anda keluar\r\n'
            self.client.send(self.login_msg)
            print 'Respon: ' + self.login_msg.strip(), self.client.getpeername()
            self.stop()
            #self.input_socket.remove(self.sock)
        else:
            self.message = '500 Perintah tidak diketahui\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)

            self.menu_log_in()
        
    def stop(self):
        self.id_exit = False
        self.client_data.close()
        self.client.close()

    def cwd_func(self):
        self.cwd = self.command.strip().split(' ')[1]
        checkDir = os.path.isdir(os.path.join(self.base, self.cwd))
        if checkDir:
            self.fullpath = os.path.join(self.base, self.cwd)
            self.message = '257 Berhasil directory listing ' + self.cwd + '\r\n'
        else:
            self.message = '550 Requested action not taken, file not found or no access. This error usually results if the client user process does not have appropriate access permissions to perform the action, or if <name> was not found.\r\n'

        print 'Respon: ' + self.message.strip(), self.client.getpeername()
        self.client.send(self.message)
        self.passive_mode()
        
    def pwd(self):
        self.message = '257 ' + self.cwd + 'is current directory.\r\n'
        print 'Respon: ' + self.message.strip(), self.client.getpeername()
        self.client.send(self.message)
        self.passive_mode()
        
    def stor(self):
        file_name = self.command.strip().partition(' ')[2]
        path = os.path.join(self.fullpath, file_name)
        #print path

        check = self.client.recv(4)
        file_size = int(self.client.recv(self.size))
        #print file_size
        data = ""
        status = ""
        if check == 'True':
            self.message = '150 File status okay; about to open data connection. Client may begin transferring data over the data connection.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            with open(path, 'wb') as berkas:
                while file_size:
                    data = self.client_data.recv(self.size)
                    berkas.write(data)
                    file_size -= len(data)
            self.message = '226 Berkas ' + file_name + ' berhasil dikirim\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        else:
            self.message = '501 Syntax error in parameters or arguments. This usually results from an invalid or missing file name.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            
        self.passive_mode()

    def retr(self):
        file_name = self.command.strip().partition(' ')[2]
        path = os.path.join(self.fullpath, file_name)
        check = os.path.isfile(path)
        file_size = os.path.getsize(path)
        print file_size
        self.client.send(str(check))
        self.client.send(str(file_size))
        data = ""
        if check:
            self.message = '150 The command was successful, data transfer starting.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            
            with open(path, 'rb') as berkas:
                while file_size:
                    data += berkas.read()
                    file_size -= len(data)
            self.client_data.sendall(data)
            self.message = '226 Berkas ' + file_name + ' berhasil dikirim\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            
        else:
            self.message = '501 Syntax error in parameters or arguments. This usually results from an invalid or missing file name.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        self.passive_mode()
        
    def rnfr(self):
        file_name = self.command.strip().split(' ')[1]
        path = os.path.join(self.fullpath, file_name)
        checkDir = os.path.isdir(path)
        checkFile = os.path.isfile(path)
        
        if checkDir:
            self.message = '350 Siap untuk RNTO directory\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            self.command = self.client.recv(self.size)
            if 'RNTO' in self.command:
                print 'Perintah: ' + self.command.strip(), self.client.getpeername()
                name = os.path.join(self.fullpath, self.command.strip().split(' ')[1]) 
                rename = os.rename(path, name)
                self.message = '250 Rename was successful.\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
            else:
                self.message = '501 Syntax error in parameters or arguments. This usually results from an invalid or missing file name.\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
            self.passive_mode()
                
        elif checkFile:
            self.message = '350 Siap untuk RNTO file\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            self.command = self.client.recv(self.size)
            if 'RNTO' in self.command:
                print 'Perintah: ' + self.command.strip(), self.client.getpeername()
                name = os.path.join(self.fullpath, self.command.strip().split(' ')[1])
                rename = os.rename(path, name)
                self.message = '250 Rename was successful.\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
            else:
                self.message = '501 Syntax error in parameters or arguments. This usually results from an invalid or missing file name.\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
            self.passive_mode()
        else:
            self.message = '501 Perintah tidak diketahui\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)

    #menu buat ngelist isi (folder dan file) di dalam shared folder ----> Franky
    def LIST(self):
        cmd = self.command.strip().split(' ')
        i = len(cmd)
        temp = ""
        if i > 1:
            checkFile = os.path.isfile(os.path.join(self.fullpath, cmd[1]))
            checkDir = os.path.isdir(os.path.join(self.fullpath, cmd[1]))
            if checkFile:
                file_size = os.path.getsize(os.path.join(self.fullpath, cmd[1]))
                print file_size
                self.client.send(str (file_size))
            elif checkDir:
                dirs = os.listdir(os.path.join(self.base, cmd[1]))
                i = 0
                for x in dirs:
                    temp += x
                    temp += '\r\n'
                    i+=1
                if i > 0:
                    print temp
                    self.client.send(temp)
                else:
                    self.message = '550 Requested action not taken, file not found, or no access\r\n'
                    print 'Respon: ' + self.message.strip(), self.client.getpeername()
                    self.client.send(self.message)
            else:
                self.message = '550 Requested action not taken, file not found, or no access\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
        else:
            dirs = os.listdir(self.fullpath)
            for x in dirs:
               temp += x
               temp += '\r\n'
            print temp.strip()
            self.client.send(temp)   
        self.passive_mode()
        
    #menu buat folder baru ------> Franky dan Ira
    def mkd(self):
        self.cmd = self.command
        self.chwd = self.cmd.strip().split(' ')[1]
        dn=os.path.join(self.fullpath, self.chwd)
        self.allow_make = os.path.isdir(dn)
        if self.allow_make:
            self.message = '550 - Requested action not taken, file not found or no access.This error usually results if the client user process does not have appropriate access permissions to perform the action.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        else:
            os.mkdir(dn)
            self.message = '250 - The command was successful.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
            
        self.passive_mode()

    #menu buat hapus folder --------> Ira 
    def rmd(self):
        self.cmd = self.command
        self.chwd = self.cmd.strip().split(' ')[1]
        dn=os.path.join(self.fullpath, self.chwd)
        self.allow_delete = os.path.isdir(dn)
        if self.allow_delete == True:
            os.rmdir(dn)
            self.message = '250 - The command was successful.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)

        else:
            self.message = '550 - Requested action not taken, file not found or no access. This error usually results if the client user process does not have appropriate access permissions to perform the action, or if <name> was not found.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        self.passive_mode()

    #menu buat hapus file -----------> Ifa
    def dele(self):
        self.cmd = self.command
        self.chwd = self.cmd.strip().split(' ')[1]
        fn=os.path.join(self.fullpath, self.chwd)
        self.allow_delete = os.path.isfile(fn)
        if self.allow_delete == True:
            os.remove(fn)
            self.message = '250 - The command was successful.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        else:
            self.message = '550 - Requested action not taken, file not found, or no access. This error usually results if the client user process does not have appropriate access permissions to perform the action, or if <name> was not found.\r\n'
            print 'Respon: ' + self.message.strip(), self.client.getpeername()
            self.client.send(self.message)
        self.passive_mode()

    #menu buat melihat list command dan penjelasannya ------> Ifa
    def helps(self):
        self.cmd  = self.command
        self.chwd = self.cmd.strip().split(' ')
        i = len(self.chwd)
        if i>1:
            if self.chwd[1] == 'STOR':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to UPLOAD.\r\nSyntax : STOR[space]filename\r\n' 
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1] == 'RETR':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to DOWNLOAD.\r\nSyntax : RETR[space]filename\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1] == 'MKD':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to MAKE NEW DIRECTORY.\r\nSyntax : MKD[space]directoryname\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'RMD':
                self.message = '214 The following commands are recognized.\r\n' +  'Command used to DELETE DIRECTORY.\r\nSyntax : RMD[space]directoryname\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'DELE':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to DELETE FILE.\r\n\nSyntax : DELE[space]filename[.extension]\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'LIST':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to LIST DIRECTORIES AND FILES IN CURRENT LOCATION.\r\nSyntax : LIST\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'PWD':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to SHOW WORKING DIRECTORY.\r\nSyntax : PWD\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'CWD':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to CHANGE WORKING DIRECTORY.\r\nSyntax : CWD[space][/]Directory\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            elif self.chwd[1]== 'RNTO':
                self.message = '214 The following commands are recognized.\r\n' + 'Command used to LIST DIRECTORIES AND FILES IN CURRENT LOCATION.\r\nSyntax : RNTO[space]directory name/filename[.extension/non-extension]\r\n'
                print 'Respon: ' + self.message, self.client.getpeername()
                self.client.send(self.message)
            else:
                self.message = '214 The following commands are not recognized in our library.\r\n'
                print 'Respon: ' + self.message.strip(), self.client.getpeername()
                self.client.send(self.message)
        else:
            self.message = '214 The following commands are recognized (* => not implemented).\r\n'
            msg = 'PWD      ==> Menunjukkan direktori sekarang\r\nLIST     ==> Menunjukkan folder dan file di dalam direktori sekarang\r\nCWD      ==> Mengubah direktori sekarang\r\nMKD      ==> Membuat direktori baru\r\nRMD      ==> Menghapus direktori\r\nRNTO     ==> Mengubah nama direktori atau file\r\nDELE     ==> Menghapus file\r\nDOWNLOAD ==> Mendownload file\r\nUPLOAD   ==> Mengupload file'
            print 'Respon: ' + self.message + msg
            self.client.sendall(self.message + msg)
        self.passive_mode()

            
        
        
        
if __name__ == "__main__":
    s = Server()
    s.run()



