import clr
clr.AddReferenceToFile("mysql.data.dll")
from MySql.Data.MySqlClient import *


class MySql:
    def __init__(self, xml):
        MyConString = "SERVER=localhost;" + "DATABASE=wiki1;" + "UID=root;" + "PASSWORD=;"
        SQLConnection = MySqlConnection(MyConString)
        SQLConnection.Open()
        SQLConnection.Ping()
