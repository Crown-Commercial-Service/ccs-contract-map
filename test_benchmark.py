import subprocess


def test_bench_mark():
    """
        Test benchmark of the 'map' endpoint, with N(change as fit) requests
        - To run, install apache benchmark tool on your machine
        - Setup a test_json.json file with dummy inputs
        - Run the FastAPI application
        - Log results
    """

    subprocess.run(["ab",
                    "-p",
                    "test_json.json",
                    "-T",
                    "application/json",
                    "-n",
                    "100000",
                    "-c",
                    "8",
                    "http://localhost:8080/map"])
