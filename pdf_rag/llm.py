from typing import Protocol

import httpx


class AnswerGenerator(Protocol):
    def answer(self, question: str, evidence: list[dict]) -> str: ...

    def health(self) -> None: ...


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 90) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def answer(self, question: str, evidence: list[dict]) -> str:
        context_parts = []
        for index, item in enumerate(evidence, start=1):
            page = f", trang {item['page']}" if item.get("page") else ""
            context_parts.append(
                f"[S{index}] {item['filename']}{page}: {item['text']}"
            )
        context = "\n\n".join(context_parts)
        prompt = (
            "Bạn là trợ lý hỏi đáp tài liệu. Chỉ trả lời bằng thông tin "
            "được hỗ trợ rõ ràng trong CONTEXT. Trích dẫn từng ý bằng mã [S1], [S2] "
            "đúng với nguồn. Nếu thiếu bằng chứng, chỉ trả lời: "
            "\"Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này.\" "
            "Không suy đoán.\n\n"
            f"CONTEXT:\n{context}\n\nCÂU HỎI: {question}"
        )
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            answer = response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("LLM không khả dụng hoặc trả về phản hồi không hợp lệ.") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("LLM trả về câu trả lời trống.")
        return answer.strip()

    def health(self) -> None:
        response = httpx.get(f"{self.base_url}/api/tags", timeout=3)
        response.raise_for_status()
        models = response.json().get("models", [])
        available = {
            item.get("name") or item.get("model")
            for item in models
            if isinstance(item, dict)
        }
        if self.model not in available:
            raise RuntimeError(f"LLM model '{self.model}' chưa được tải.")
