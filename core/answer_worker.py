# filepath: core/answer_worker.py
from PySide6.QtCore import QThread, Signal, Slot
from core.llm_client import call_llm, process_llm_answer 

class AnswerWorker(QThread):
    finished_question = Signal(int, list)
    log_signal = Signal(str)

    def __init__(self, questions_data):
        super().__init__()
        self.questions_data = questions_data
        self._is_running = True

    def run(self):
        self.log_signal.emit("后台答题线程已启动，开启全速模式...")
        
        for q_data in self.questions_data:
            # 每次循环开始前检查是否被叫停
            if not self._is_running:
                self.log_signal.emit("-> 答题已被用户手动中止！")
                break 

            q_index = q_data['index']
            question = q_data['question']
            has_options = q_data['hasOptions']
            ai_choice = q_data['choices']

            self.log_signal.emit(f"-> 正在处理第 {q_index + 1} 题: {question[:15]}...")

            if not has_options:
                answer_text = call_llm(question)
                self.log_signal.emit(f"[第{q_index + 1}题 - 简答] {answer_text}")
            else:
                raw_response = call_llm(question, ai_choice)
                
                # 【核心防呆】：从长耗时的 API 接口回来后，再次检查是否被用户叫停！
                # 如果此时发现被叫停了，立刻抛弃结果，直接退出循环
                if not self._is_running:
                    self.log_signal.emit("-> 答题已被中止，取消点击操作。")
                    break
                    
                self.log_signal.emit(f"  [AI 原始输出]: {raw_response}")

                final_answer = process_llm_answer(ai_choice, raw_response)
                self.log_signal.emit(f"[第{q_index+1}题] 提取答案: 选 {final_answer}")
                self.finished_question.emit(q_index, final_answer)


        if self._is_running:
            self.log_signal.emit("-> 批次题目已全部处理并点击完毕！")
        
    def stop(self):
        self._is_running = False