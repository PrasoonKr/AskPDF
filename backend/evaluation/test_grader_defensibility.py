import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))

from backend.adaptive.grader import RelevanceGrader

class MockDoc:
    def __init__(self, text: str, score: float = 0.5):
        self.text = text
        self.score = score

# -----------------------------------------------------------------------------
# 60 EVALUATION SAMPLES
# -----------------------------------------------------------------------------

# Category 1: 20 Truly Relevant Pairs
RELEVANT_SAMPLES = [
    ("What is normalization in DBMS?", "LEC-11: Normalisation is a step towards DB optimisation. It eliminates redundancy through decomposition.", 0.85),
    ("Explain first normal form 1NF", "1NF requires each attribute in a relation to be atomic, meaning no repeating groups or multivalued attributes.", 0.82),
    ("What is BCNF Boyce-Codd Normal Form?", "A relation R is in BCNF if for every functional dependency X -> Y, X is a super key of R.", 0.88),
    ("Explain Armstrong's Axioms in functional dependency", "Armstrong's axioms include Reflexivity, Augmentation, and Transitivity, used to infer all FDs on a relation.", 0.79),
    ("What is database sharding?", "Database sharding is a horizontal partitioning technique that divides a single dataset across multiple servers.", 0.84),
    ("What is vertical partitioning?", "Vertical partitioning splits a table by columns, separating rarely accessed wide columns from frequently accessed ones.", 0.81),
    ("What is the CAP theorem?", "CAP theorem states that a distributed system can only guarantee at most two out of Consistency, Availability, and Partition tolerance.", 0.90),
    ("What is write-through caching?", "In write-through cache, data is simultaneously written to the cache and the underlying database before acknowledging success.", 0.83),
    ("Explain ACID properties in database transactions", "ACID stands for Atomicity, Consistency, Isolation, and Durability, ensuring reliable database transaction processing.", 0.87),
    ("What is a primary key in relational databases?", "A primary key is a column or set of columns that uniquely identifies each row in a database table with no null values.", 0.86),
    ("What is an index in DBMS?", "An index is a data structure, typically a B+ tree, that improves the speed of data retrieval operations on a table.", 0.80),
    ("Explain database deadlocks and detection", "A deadlock occurs when two or more transactions hold locks on resources that each other requires to proceed.", 0.78),
    ("What is two-phase locking 2PL?", "2PL is a concurrency control protocol consisting of an expanding phase where locks are acquired and a shrinking phase.", 0.82),
    ("What is consistent hashing in distributed systems?", "Consistent hashing maps both keys and nodes to a circular hash ring to minimize key remapping when nodes join or leave.", 0.89),
    ("What is a reverse proxy?", "A reverse proxy sits in front of web servers and forwards client requests to those web servers for load balancing and caching.", 0.84),
    ("Explain master-slave replication", "Master-slave replication designates one primary server for writes and replicates the data to read-only replicas.", 0.83),
    ("What is database denormalization?", "Denormalization is the intentional introduction of redundancy into a database design to reduce join overhead and improve read speed.", 0.80),
    ("What is an entity relationship diagram ERD?", "An ER diagram visually models entities, their attributes, and relationships between tables in database design.", 0.77),
    ("What is a Foreign Key constraint?", "A foreign key is a field that links to the primary key of another table to enforce referential integrity.", 0.85),
    ("What is rate limiting in system design?", "Rate limiting controls the incoming network traffic rate to protect services from abuse, DDoS, and starvation.", 0.82),
]

# Category 2: 20 Adversarial Pairs (Contain query keywords, but context explicitly disclaims or is irrelevant)
ADVERSARIAL_SAMPLES = [
    ("What is normalization in DBMS?", "Normalization was intentionally skipped in this project because we chose MongoDB, which relies strictly on denormalized embedded documents.", 0.15),
    ("Explain first normal form 1NF", "We will not discuss first normal form 1NF today. Instead, refer to chapter 10 for details while we move directly to B-trees.", 0.12),
    ("What is BCNF Boyce-Codd Normal Form?", "BCNF is not supported in our schema. For information on BCNF, consult external database theory textbooks.", 0.10),
    ("Explain Armstrong's Axioms in functional dependency", "Functional dependency and Armstrong's axioms are omitted from the syllabus for this semester.", 0.08),
    ("What is database sharding?", "Sharding was once considered but rejected. This chapter focuses exclusively on vertical hardware scaling.", 0.14),
    ("What is vertical partitioning?", "Partitioning is not used in this architecture. All data resides in a single monolithic table without vertical separation.", 0.09),
    ("What is the CAP theorem?", "While some mention CAP theorem, this section is strictly an introduction to basic CSS and HTML styling rules.", 0.05),
    ("What is write-through caching?", "Caching strategies like write-through are outside the scope of this hardware manual.", 0.07),
    ("Explain ACID properties in database transactions", "ACID transactions are not provided by this key-value cache, which offers no consistency guarantees.", 0.11),
    ("What is a primary key in relational databases?", "A primary key was removed from the table schema due to legacy constraints; no primary key definition exists.", 0.08),
    ("What is an index in DBMS?", "Index creation failed during maintenance. To troubleshoot disk drive space, check the system logs.", 0.10),
    ("Explain database deadlocks and detection", "Deadlocks are ignored by this lock-free memory allocator which does not support database operations.", 0.06),
    ("What is two-phase locking 2PL?", "Two-phase locking 2PL is deprecated in our engine; refer to chapter 4 for optimistic concurrency instead.", 0.12),
    ("What is consistent hashing in distributed systems?", "Consistent hashing is mentioned in the glossary, but this paper only evaluates round-robin load balancers.", 0.09),
    ("What is a reverse proxy?", "A reverse proxy was replaced by direct IP routing; no reverse proxy configurations are described here.", 0.08),
    ("Explain master-slave replication", "Master-slave replication was disabled across all clusters due to networking bandwidth limitations.", 0.11),
    ("What is database denormalization?", "Denormalization is strictly forbidden by company policy; no denormalization examples will be shown.", 0.07),
    ("What is an entity relationship diagram ERD?", "An ER diagram is not applicable to unstructured document stores and will not be covered in this unit.", 0.06),
    ("What is a Foreign Key constraint?", "Foreign key constraints were disabled to speed up bulk data loading without validating referential integrity.", 0.13),
    ("What is rate limiting in system design?", "Rate limiting is completely absent in this internal staging environment; use firewalls instead.", 0.08),
]

# Category 3: 20 Completely Irrelevant / Off-Topic Pairs (Zero keyword or topic overlap)
IRRELEVANT_SAMPLES = [
    ("What is normalization in DBMS?", "The kinematics equations describe the motion of an object with constant linear acceleration.", 0.01),
    ("Explain first normal form 1NF", "Photosynthesis in green plants converts light energy into chemical energy stored in glucose.", 0.00),
    ("What is BCNF Boyce-Codd Normal Form?", "Newton's second law states that force equals the time derivative of momentum.", 0.02),
    ("Explain Armstrong's Axioms in functional dependency", "The French Revolution began in 1789 with the storming of the Bastille in Paris.", 0.01),
    ("What is database sharding?", "Mitochondria are the powerhouses of eukaryotic cells, generating cellular adenosine triphosphate.", 0.00),
    ("What is vertical partitioning?", "In Shakespeare's Hamlet, the protagonist contemplates existence in his famous soliloquy.", 0.01),
    ("What is the CAP theorem?", "Baking sourdough bread requires flour, water, salt, and a wild yeast fermentation starter.", 0.00),
    ("What is write-through caching?", "The solar system consists of the Sun and planetary bodies orbiting within its gravitational field.", 0.02),
    ("Explain ACID properties in database transactions", "Organic chemistry studies the structure, properties, and reactions of carbon-based compounds.", 0.01),
    ("What is a primary key in relational databases?", "Plate tectonics explains the structure and motion of Earth's lithosphere over geological time.", 0.00),
    ("What is an index in DBMS?", "The Renaissance was a fervent period of European cultural, artistic, and economic rebirth.", 0.02),
    ("Explain database deadlocks and detection", "A sonnet is a poetic form consisting of 14 lines written in iambic pentameter with a set rhyme.", 0.01),
    ("What is two-phase locking 2PL?", "Thermodynamics first law states that energy can neither be created nor destroyed, only transformed.", 0.00),
    ("What is consistent hashing in distributed systems?", "The Great Barrier Reef off Queensland, Australia, is the world's largest coral reef ecosystem.", 0.01),
    ("What is a reverse proxy?", "The human circulatory system uses the heart and blood vessels to distribute oxygenated blood.", 0.00),
    ("Explain master-slave replication", "Igneous rocks form through the cooling and solidification of molten magma or lava.", 0.02),
    ("What is database denormalization?", "The periodic table arranges chemical elements by atomic number and recurring chemical properties.", 0.01),
    ("What is an entity relationship diagram ERD?", "Impressionism in art emphasizes accurate depiction of light and ordinary subject matter.", 0.00),
    ("What is a Foreign Key constraint?", "The speed of light in vacuum is approximately 299,792,458 meters per second.", 0.01),
    ("What is rate limiting in system design?", "Cellular mitosis divides a single parent cell into two identical daughter cells for growth.", 0.00),
]

def run_grader_defensibility_benchmark():
    print("=" * 75)
    print("  AskPDF Relevance Grader Defensibility Benchmark (60 Samples)")
    print("  - 20 Truly Relevant Pairs")
    print("  - 20 Adversarial Pairs (Keyword Overlap but Non-Relevant / Disclaimer)")
    print("  - 20 Completely Off-Topic Pairs")
    print("=" * 75)

    # Initialize grader with local LLM fallback service for deep validation
    from backend.llm.client import OllamaClient
    from backend.llm.service import LLMService
    llm = LLMService(OllamaClient())
    grader = RelevanceGrader(llm_service=llm, score_threshold=0.15)

    results = []
    
    all_samples = (
        [(q, p, s, True, "Relevant") for q, p, s in RELEVANT_SAMPLES] +
        [(q, p, s, False, "Adversarial") for q, p, s in ADVERSARIAL_SAMPLES] +
        [(q, p, s, False, "Off-Topic") for q, p, s in IRRELEVANT_SAMPLES]
    )

    t0 = time.time()
    for idx, (query, passage, score, expected, category) in enumerate(all_samples, 1):
        doc = MockDoc(text=passage, score=score)
        t_start = time.time()
        grade = grader.grade(query, [doc])
        dur = time.time() - t_start

        actual = grade.is_relevant
        correct = (actual == expected)

        results.append({
            "idx": idx,
            "category": category,
            "query": query,
            "expected": expected,
            "actual": actual,
            "correct": correct,
            "reason": grade.reasoning,
            "latency": dur,
        })
        
        status_icon = "PASS" if correct else "FAIL"
        print(f"[{status_icon}] Sample {idx:02d} ({category:11s}) | Expected: {str(expected):5s} | Got: {str(actual):5s} | Latency: {dur*1000:6.1f}ms", flush=True)

    total_time = time.time() - t0

    # Metrics computation
    tp = sum(1 for r in results if r["expected"] and r["actual"])
    fp = sum(1 for r in results if not r["expected"] and r["actual"])
    tn = sum(1 for r in results if not r["expected"] and not r["actual"])
    fn = sum(1 for r in results if r["expected"] and not r["actual"])

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(results)

    # Category breakdowns
    rel_acc = sum(1 for r in results if r["category"] == "Relevant" and r["correct"]) / 20.0
    adv_acc = sum(1 for r in results if r["category"] == "Adversarial" and r["correct"]) / 20.0
    off_acc = sum(1 for r in results if r["category"] == "Off-Topic" and r["correct"]) / 20.0

    print("\n" + "=" * 75)
    print("  CONFUSION MATRIX & DEFICIENCY ANALYSIS")
    print("=" * 75)
    print(f"  True Positives  (TP) : {tp:2d} / 20 (Correctly accepted relevant documents)")
    print(f"  True Negatives  (TN) : {tn:2d} / 40 (Correctly rejected noise & adversarial text)")
    print(f"  False Positives (FP) : {fp:2d} / 40 (Irrelevant text mistakenly accepted)")
    print(f"  False Negatives (FN) : {fn:2d} / 20 (Relevant text mistakenly rejected)")
    print("-" * 75)
    print(f"  Precision          : {precision*100:6.2f}%")
    print(f"  Recall             : {recall*100:6.2f}%")
    print(f"  F1 Score           : {f1*100:6.2f}%")
    print(f"  Overall Accuracy   : {accuracy*100:6.2f}%")
    print("-" * 75)
    print(f"  Accuracy by Category:")
    print(f"    - Truly Relevant Documents                  : {rel_acc*100:5.1f}%")
    print(f"    - Adversarial (Keyword-Overlapping Noise)   : {adv_acc*100:5.1f}%")
    print(f"    - Completely Off-Topic Noise               : {off_acc*100:5.1f}%")
    print(f"  Total Benchmark Time: {total_time:.2f}s (Avg {total_time/60*1000:.1f}ms / evaluation)")
    print("=" * 75)

if __name__ == "__main__":
    run_grader_defensibility_benchmark()
