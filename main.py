from allegribot import AllegriBot

tokenfile = open('token.txt', 'r')
lines = tokenfile.readlines()
token = lines[0]
tokenfile.close()

maxBot = AllegriBot(token)

def main():
    maxBot.run()

if __name__ == "__main__":
    main()
