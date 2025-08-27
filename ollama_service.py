import datetime
import time
import traceback

import ollama
from transformers import AutoTokenizer
import core.database as storage




class Maester:

    def ollama_call(self, job_id, params):

        try:

            start = datetime.datetime.now()

            input_content = [{"role": "system", "content": params['template']}, {"role": "user", "content":params['content']}]

            response = ollama.chat(
                params['agent'],
                input_content,
            )

            full_response = response['message']['content']

            # gravação de uso
            total_s = (datetime.datetime.now() - start).total_seconds() * 1_000_000_000
            output_tokens = self.count_tokens_qwen(full_response)
            input_tokens = self.count_tokens_qwen(str(input_content))

            total_tokens = input_tokens + output_tokens

            data = storage.ia_usage()
            if not isinstance(data, list):
                data = []

            data.append({
                "date": str(start),
                "total_seconds": total_s,
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model_name": params['agent'],
            })

            storage.ia_usage(data)
            self.completed_job(job_id, full_response)
        except:
            self.error_job(job_id, traceback.format_exc())


    def master_queue(self):


        while True:

            data = storage.queue()
            if not isinstance(data, dict):
                data = {}

            s_queue = list(data.keys())

            if len(s_queue) == 0:
                print("FILA VAZIA")

            else:

                for job_id in s_queue:

                    if data[job_id]["STATE"] == "ON QUEUE":

                        self.update_status(job_id, "RUNNING")
                        self.ollama_call(job_id, data[job_id]["PARAMS"])

                print("FILA EM EXECUÇÃO")

            time.sleep(1)


    def update_status(self, job_id, state):

        data = storage.queue()
        data[job_id]["STATE"] = state
        storage.queue(data)


    def completed_job(self, job_id, resonse):
        data = storage.queue()
        data[job_id]["RESULT"] = resonse
        data[job_id]["STATE"] = "COMPLETE"
        storage.queue(data)

    def error_job(self, job_id, error):
        data = storage.queue()
        data[job_id]["RESULT"] = error
        data[job_id]["STATE"] = 'ERROR'
        storage.queue(data)


    def count_tokens_qwen(self, text):
        try:
            tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B", trust_remote_code=True)
            return len(tokenizer.encode(text))
        except:
            return len(str(text).split(" "))



if __name__ == "__main__":

    maester = Maester()
    maester.master_queue()


