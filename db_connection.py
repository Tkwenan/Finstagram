import pymysql.cursors



#conn = pymysql.connect( host='localhost',
#                       port = 3306,
#                        user='root', #replace with your db username
#                       password='blackish', #replace with your password
#                        db='finstagram_connect',  #replace with your db name            
#                        charset='utf8mb4',
#                        cursorclass=pymysql.cursors.DictCursor)

# conn = pymysql.connect(host='LAPTOP-RAG0B066',
#                        port=3306,
#                        user='jude',  # replace with your db username
#                        password='judeofosu',  # replace with your password
#                        db='finstagram_connect',  # replace with your db name
#                        charset='utf8mb4',
#                        cursorclass=pymysql.cursors.DictCursor)

conn = pymysql.connect(host='Srashtas-MacBook-Pro.local',
                    port = 3306,
                    user='root', #replace with your db username
                    password='Srashtaexo40181', #replace with your password
                    db='finstagram_connect',  #replace with your db name
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor)
