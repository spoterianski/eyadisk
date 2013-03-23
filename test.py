#!/usr/bin/env python
#encoding:UTF-8
import eyadisk

def main():

    user = 'username'
    pwd = 'password'

    api = eyadisk.EYaDisk(user=user, pwd=pwd)
    api.mkdir('eyadisk')
    api.upload('README.MD', '/eyadisk/README.MD')
    print api.publish('/eyadisk/README.MD')

if __name__ == '__main__':
	main()
