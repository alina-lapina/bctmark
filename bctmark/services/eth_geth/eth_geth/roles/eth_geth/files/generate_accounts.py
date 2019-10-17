from web3.auto import w3

for x in range(0, 5):
    w3.personal.newAccount("password")

for x in w3.eth.accounts:
    print(x)
