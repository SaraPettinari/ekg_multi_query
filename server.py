from neo4j import GraphDatabase
from flask import Flask, current_app


class HelloWorldExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def print_graph(self):
        with self.driver.session() as session:
            actors = session.execute_write(
                self._create_and_return_data, actor='drone')
            for record in actors:
                print(record)
                
        session.close()

    @staticmethod
    def _create_and_return_data(tx, actor):
        result = tx.run(
            """MATCH (e1:Event) 
                WHERE e1.Actor = $actor
                RETURN e1""", actor=actor)
        return [record["e1"] for record in result]


if __name__ == "__main__":
    greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "12341234")
    greeter.print_graph()
    greeter.close()
