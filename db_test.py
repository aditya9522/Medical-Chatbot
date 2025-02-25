from neo4j import GraphDatabase

NEO4J_URI='neo4j+s://5f4ce6c9.databases.neo4j.io'
NEO4J_USER='neo4j'
NEO4J_PASSWORD='WYecDK9AE_WowVLHS5RdgShx6qv6jRndJrsUhUX448U'

class Neo4jEHR:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    

db = Neo4jEHR(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
print(db)



