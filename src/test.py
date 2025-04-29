
def test(s, word):
    print(s.find(word), s[:s.find(word)])
    
test("ticket to norwich", "norwich")