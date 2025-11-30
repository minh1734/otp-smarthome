import pymysql
def connminh():
	return pymysql.connect(
		host="mrbeast-tomminhlequang-c6cf.d.aivencloud.com",
		port=12981,
		user="avnadmin",
		password=os.getenv("AIVEN_PASSWORD"),
		database="defaultdb",
		ssl={"ssl": {}}
	)
