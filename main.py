import os
import json
# from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from  dotenv import load_dotenv

load_dotenv()

# Access environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

JSON_FILE_PATH = "dataset/Cleaned_EhrRecords (3).json"


# class Neo4jConnection:
#     def __init__(self, uri, username, password):
#         try:
#             self.driver = GraphDatabase.driver(uri, auth=(username, password))
#             self.driver.verify_connectivity()
#             print("Connected to Neo4j Aura successfully!")
#         except Exception as e:
#             raise ConnectionError(f"Failed to connect to Neo4j: {e}")

#     def query(self, query, params=None):
#         try:
#             with self.driver.session() as session:
#                 result = session.run(query, params or {})
#                 return result.data()
#         except Exception as e:
#             raise RuntimeError(f"Error executing query: {e}")

#     def get_structured_schema(self):
#         try:
#             with self.driver.session() as session:
#                 node_props_query = """
#                 MATCH (n)
#                 WITH DISTINCT labels(n) AS labels, keys(n) AS keys
#                 UNWIND labels AS label
#                 UNWIND keys AS key
#                 RETURN label, collect(DISTINCT key) AS properties
#                 """
#                 node_props = session.run(node_props_query).data()

#                 rel_props_query = """
#                 MATCH ()-[r]->()
#                 WITH DISTINCT type(r) AS type, keys(r) AS keys
#                 UNWIND keys AS key
#                 RETURN type, collect(DISTINCT key) AS properties
#                 """
#                 rel_props = session.run(rel_props_query).data()

#                 structured_schema = {
#                     "node_props": {item["label"]: item["properties"] for item in node_props},
#                     "rel_props": {item["type"]: item["properties"] for item in rel_props},
#                 }
#                 return structured_schema
#         except Exception as e:
#             raise RuntimeError(f"Error retrieving schema: {e}")

#     def close(self):
#         self.driver.close()
#         print("Neo4j connection closed.")
        
def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found at: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")

def load_healthcare_data(json_data, neo4j_ehr):
    for record in json_data:
        resource_type = record.get("resourceType")

        if resource_type == "Patient":
            patient_query = """
            MERGE (p:Patient {id: $id})
            SET p.name = $name,
                p.gender = $gender,
                p.birthDate = $birthDate,
                p.maritalStatus = $maritalStatus
            WITH p
            UNWIND $telecom as tel
            MERGE (t:Telecom {value: tel.value})
            SET t.system = tel.system,
                t.use = tel.use,
                t.rank = tel.rank
            MERGE (p)-[:HAS_TELECOM]->(t)
            WITH p
            UNWIND $address as addr
            MERGE (a:Address {line: coalesce(addr.line[0], 'Unknown')})
            SET a.city = addr.city,
                a.state = addr.state,
                a.postalCode = addr.postalCode,
                a.country = addr.country,
                a.use = addr.use
            MERGE (p)-[:HAS_ADDRESS]->(a)
            """
            neo4j_ehr.query(patient_query, record)

        elif resource_type == "Condition" and record.get("patient_id"):
            condition_query = """
            MERGE (c:Condition {id: $id})
            SET c.condition_name = $condition_name,
                c.clinicalStatus = $clinicalStatus,
                c.verificationStatus = $verificationStatus,
                c.severity = $severity,
                c.onsetDateTime = $onsetDateTime,
                c.recordedDate = $recordedDate
            WITH c
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_CONDITION]->(c)
            """
            neo4j_ehr.query(condition_query, record)

        elif resource_type == "Observation" and record.get("patient_id"):
            observation_query = """
            MERGE (o:Observation {id: $id})
            SET o.category = $category,
                o.code = $code,
                o.effectiveDateTime = $effectiveDateTime,
                o.value = $value,
                o.unit = $unit
            WITH o
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_OBSERVATION]->(o)
            """
            neo4j_ehr.query(observation_query, record)

        elif resource_type == "MedicationStatement" and record.get("patient_id"):
            medication_query = """
            MERGE (m:MedicationStatement {id: $id})
            SET m.medication = $medication,
                m.status = $status,
                m.dosage = $dosage
            WITH m
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_MEDICATION]->(m)
            """
            neo4j_ehr.query(medication_query, record)

        elif resource_type == "DiagnosticReport" and record.get("patient_id"):
            report_query = """
            MERGE (d:DiagnosticReport {id: $id})
            SET d.test_name = $test_name,
                d.status = $status,
                d.effectiveDateTime = $effectiveDateTime
            WITH d
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_DIAGNOSTIC_REPORT]->(d)
            """
            neo4j_ehr.query(report_query, record)

        elif resource_type == "AllergyIntolerance" and record.get("patient_id"):
            allergy_query = """
            MERGE (a:AllergyIntolerance {id: $id})
            SET a.code = $code,
                a.clinicalStatus = $clinicalStatus,
                a.verificationStatus = $verificationStatus
            WITH a
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_ALLERGY]->(a)
            """
            neo4j_ehr.query(allergy_query, record)

        elif resource_type == "Immunization" and record.get("patient_id"):
            immunization_query = """
            MERGE (i:Immunization {id: $id})
            SET i.vaccine = $vaccine,
                i.status = $status,
                i.occurrenceDateTime = $occurrenceDateTime,
                i.manufacturer = $manufacturer
            WITH i
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_IMMUNIZATION]->(i)
            """
            neo4j_ehr.query(immunization_query, record)

def initialize_chatbot(graph):
    prompt = PromptTemplate(
        input_variables=["question", "context"],
        template=(
            "You are a healthcare assistant with access to patient data. "
            "If the user's message is a greeting like 'hi', 'hello', or 'hey', respond with: "
            "'Hello! How can I help you find patients and their details?' "
            "Otherwise, if the user's message is related to patients, use the following data: {context} "
            "to provide a human-readable response. For example, list patients with their names and details if applicable. "
            "Always assume you know the answer and respond confidently. "
            "User's query: {question}"
        ),
    )
    
    try:
        # llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
        llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            qa_prompt=prompt,
            verbose=True,
            return_intermediate_steps=True, # for debugging
            allow_dangerous_requests=True
        )
        return chain
    except Exception as e:
        raise RuntimeError(f"Failed to initialize chatbot: {e}")

def generate_response(chain, prompt):
    try:
        response = chain.invoke({"query": prompt})

        # get intermediate steps
        intermediate_steps = response.get("intermediate_steps", [])
        for step in intermediate_steps:
            print(step)
            
        return response.get("result", "No response returned.")
    except Exception as e:
        return f"Error generating response: {e}"
    
def invokeChatbot(prompt):
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD) 
    chain = initialize_chatbot(graph)
    
    return generate_response(chain, prompt)
    

def main():
    # graph = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD) 

    try:
        # json_data = load_json(JSON_FILE_PATH)
        # print(f"Loaded {len(json_data)} records from JSON.")

        # load_healthcare_data(json_data, graph)
        # print("Data loaded into Neo4j successfully.")

        chain = initialize_chatbot(graph)

        query = "Give patient information which medication has been completed?"
        response = generate_response(chain, query)
        print("Response:", response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()