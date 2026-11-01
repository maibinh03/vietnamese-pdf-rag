# 📄 Vietnamese PDF RAG - Document Q&A

Ứng dụng RAG cho phép người dùng đặt câu hỏi bằng tiếng Việt dựa trên nội dung tài liệu PDF hoặc TXT. Thay vì phải đọc toàn bộ tài liệu để tìm thông tin, người dùng chỉ cần upload file và đặt câu hỏi. Hệ thống sẽ tìm các đoạn nội dung liên quan, sử dụng chúng làm context cho LLM và trả về câu trả lời kèm trích dẫn nguồn.

Dự án được xây dựng nhằm tạo ra một pipeline RAG hoàn chỉnh, từ xử lý tài liệu, embedding, semantic search đến generation và source citation. Các file trong `data/samples/` là dữ liệu giả lập do ai gen phục vụ demo, không giới hạn lĩnh vực tài liệu có thể sử dụng.

## 🛠 Tech Stack

**Python, FastAPI** cho backend API;  
**Sentence Transformers (`intfloat/multilingual-e5-small`)** để tạo multilingual embeddings;  
**Qdrant** cho vector storage và semantic search;  
**Ollama (`qwen2.5:3b`)** để tạo câu trả lời;  
**SQLite** quản lý metadata và **Docker Compose** để triển khai các dịch vụ.  

## ✨ Features

Hệ thống hỗ trợ upload PDF và TXT UTF-8, tự động trích xuất nội dung, chia chunk và tạo embedding để lập chỉ mục. Khi nhận câu hỏi, hệ thống tìm kiếm các đoạn liên quan bằng Qdrant với `top_k` và similarity threshold có thể cấu hình.

LLM chỉ được gọi khi retrieval tìm thấy đủ bằng chứng. Nếu không, hệ thống sẽ từ chối trả lời. Các câu trả lời có citation trỏ về tài liệu, trang (nếu có), chunk và vị trí ký tự trong văn bản nguồn.

API cũng cung cấp document management và health check để theo dõi trạng thái các dependency.

## ⚙️ RAG Pipeline

Quy trình gồm bốn bước: 
  **Ingestion** (trích xuất và chia chunk),  
  **Indexing** (embedding và lưu vector vào Qdrant),  
  **Retrieval** (tìm các đoạn liên quan đến câu hỏi),
  **Generation** (tạo câu trả lời dựa trên bằng chứng truy xuất được).

Metadata tài liệu được lưu trong SQLite, trong khi vector và thông tin nguồn của từng chunk được quản lý bởi Qdrant.

## 🚀 API & Usage

Ứng dụng cung cấp các endpoint `POST /documents` để upload tài liệu, `GET /documents` để xem danh sách tài liệu, `POST /chat` để đặt câu hỏi và `GET /health` để kiểm tra trạng thái dịch vụ.

Ví dụ upload và đặt câu hỏi:

```powershell
curl.exe -X POST http://localhost:8000/documents -F "file=@guide.pdf"

curl.exe -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d "{`"question`":`"Tài liệu nói về cái gì?`",`"top_k`":5}"
```

Phản hồi chat bao gồm `answer`, `abstained`, `citations` và thời gian retrieval/generation. API có giới hạn kích thước và định dạng file; PDF scan chưa được hỗ trợ  vì chưa tích hợp OCR.

## 📊 Evaluation

Bộ đánh giá gồm 100 câu hỏi, chia thành nhóm có thể trả lời trực tiếp, cần kết hợp thông tin trong và ngoài phạm vi dữ liệu.

Kết quả **TF-IDF retrieval baseline offline** trên corpus mẫu:

- Recall@5: **1.000** (75 câu có đáp án).
- Evidence Coverage @ 0.20: **0.947**.
- Correct Abstention: **0.840** (25 câu ngoài phạm vi).
- Median / P95 Latency: **0.578 / 0.723 ms**.

Lưu ý: Đây chỉ là kết quả của TF-IDF baseline chạy trên các chunk trong bộ nhớ, không phải kết quả của pipeline E5 + Qdrant + Ollama. Accuracy của generation và grounding hiện chưa được đánh giá.

## 🐳 Run with Docker

Yêu cầu Docker Compose v2. Tại thư mục dự án, tạo `.env` từ `.env.example` nếu chưa có, sau đó chạy:

```powershell
docker compose up --build -d
docker compose exec ollama ollama pull qwen2.5:3b
```

Embedding model sẽ được tải tự động trong lần chạy đầu tiên. Sau khi các dependency sẵn sàng, API có thể truy cập tại `http://localhost:8000`.

## 💡 What I Learned

Qua dự án này, mình hiểu rõ hơn cách các thành phần trong một RAG pipeline phối hợp với nhau. Đặc biệt, chất lượng retrieval ảnh hưởng trực tiếp đến câu trả lời của LLM; citation cần được duy trì xuyên suốt quá trình xử lý tài liệu và cơ chế abstention giúp hạn chế những câu trả lời thiếu căn cứ.

Mình cũng học được cách quản lý dependency giữa môi trường Docker và local, cũng như tách biệt việc đánh giá retrieval, generation và grounding thay vì chỉ dựa vào một chỉ số tổng thể.

## 🔭 Future Improvements

Một số hướng phát triển tiếp theo là tích hợp OCR cho PDF scan, thử nghiệm reranker, hiệu chỉnh similarity threshold, bổ sung đánh giá generation/grounding và xây dựng giao diện web. Nếu mở rộng triển khai, hệ thống cũng cần authentication, phân quyền tài liệu và hàng đợi xử lý ingest bất đồng bộ.

## 🎬 Demo

Video demo sẽ được cập nhật sau.
