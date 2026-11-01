import json
from pathlib import Path

OUTPUT = Path(__file__).with_name("questions.json")

FACTS = [
    ("digital_banking.txt", "Khách hàng từ 18 tuổi trở lên có thể đăng ký tài khoản thanh toán trên ứng dụng.", "Ai đủ tuổi để đăng ký tài khoản trên ứng dụng?", "Người 18 tuổi trở lên có thể đăng ký tài khoản thanh toán trên ứng dụng."),
    ("digital_banking.txt", "Khi đăng ký cần căn cước công dân còn hiệu lực và số điện thoại đang sử dụng.", "Cần chuẩn bị giấy tờ và thông tin nào khi đăng ký?", "Cần căn cước công dân còn hiệu lực và số điện thoại đang sử dụng."),
    ("digital_banking.txt", "Một số điện thoại chỉ được đăng ký cho một tài khoản.", "Một số điện thoại dùng đăng ký được mấy tài khoản?", "Mỗi số điện thoại chỉ đăng ký được một tài khoản."),
    ("digital_banking.txt", "Chuyển tiền giữa hai tài khoản MauBank trên ứng dụng miễn phí.", "Chuyển khoản nội bộ qua ứng dụng có mất phí không?", "Không. Chuyển tiền giữa hai tài khoản MauBank trên ứng dụng miễn phí."),
    ("digital_banking.txt", "Chuyển tiền nội bộ trên ứng dụng hoạt động 24/7.", "Chuyển tiền nội bộ có hoạt động vào cuối tuần không?", "Có. Dịch vụ hoạt động 24/7."),
    ("digital_banking.txt", "Chuyển tiền nhanh đến ngân hàng khác dưới 2.000.000 đồng có phí 1.000 đồng.", "Phí chuyển nhanh liên ngân hàng cho giao dịch 1 triệu đồng là bao nhiêu?", "Phí là 1.000 đồng cho giao dịch dưới 2.000.000 đồng."),
    ("digital_banking.txt", "Giao dịch chuyển nhanh liên ngân hàng từ 2.000.000 đồng có phí 0,03%, tối đa 25.000 đồng.", "Phí chuyển nhanh liên ngân hàng từ 2 triệu đồng được tính thế nào?", "Phí bằng 0,03% số tiền, tối đa 25.000 đồng."),
    ("digital_banking.txt", "Hạn mức chuyển tiền mặc định là 100.000.000 đồng mỗi ngày.", "Hạn mức chuyển tiền mặc định mỗi ngày là bao nhiêu?", "Hạn mức mặc định là 100.000.000 đồng mỗi ngày."),
    ("digital_banking.txt", "Có thể yêu cầu điều chỉnh hạn mức tại quầy sau khi xác minh danh tính.", "Làm sao để yêu cầu tăng hạn mức chuyển tiền?", "Yêu cầu điều chỉnh tại quầy sau khi xác minh danh tính."),
    ("digital_banking.txt", "Thanh toán điện, nước và internet trên ứng dụng không thu phí dịch vụ.", "Thanh toán hóa đơn điện qua ứng dụng có mất phí không?", "Không thu phí dịch vụ khi thanh toán điện, nước và internet trên ứng dụng."),
    ("digital_banking.txt", "Thanh toán hóa đơn được thực hiện hàng ngày từ 00:00 đến 23:00.", "Khung giờ thanh toán hóa đơn là khi nào?", "Hàng ngày từ 00:00 đến 23:00."),
    ("digital_banking.txt", "Hỗ trợ trên ứng dụng hoạt động 24/7.", "Tôi có thể gửi yêu cầu hỗ trợ ngoài giờ hành chính không?", "Có. Hỗ trợ trên ứng dụng hoạt động 24/7."),
    ("digital_banking.txt", "Thời gian phản hồi mục tiêu cho yêu cầu hỗ trợ là trong một ngày làm việc.", "Mục tiêu thời gian phản hồi yêu cầu hỗ trợ là bao lâu?", "Trong một ngày làm việc."),
    ("fees_and_cards.txt", "Phí duy trì tài khoản thanh toán là 0 đồng mỗi tháng.", "Phí duy trì tài khoản hàng tháng bao nhiêu?", "0 đồng mỗi tháng."),
    ("fees_and_cards.txt", "Số dư tối thiểu để duy trì tài khoản là 0 đồng.", "Tài khoản cần số dư tối thiểu bao nhiêu để duy trì?", "Không yêu cầu số dư tối thiểu; mức duy trì là 0 đồng."),
    ("fees_and_cards.txt", "Phí phát hành thẻ ghi nợ vật lý lần đầu là 50.000 đồng.", "Phí phát hành thẻ ghi nợ vật lý lần đầu bao nhiêu?", "50.000 đồng."),
    ("fees_and_cards.txt", "Phí thường niên thẻ ghi nợ là 60.000 đồng mỗi năm.", "Phí thường niên thẻ ghi nợ là bao nhiêu?", "60.000 đồng mỗi năm."),
    ("fees_and_cards.txt", "Cấp lại thẻ do mất hoặc hỏng có phí 30.000 đồng mỗi lần.", "Phí cấp lại thẻ bị mất là bao nhiêu?", "30.000 đồng mỗi lần."),
    ("fees_and_cards.txt", "Thẻ ghi nợ ảo không thu phí phát hành và không thu phí thường niên.", "Thẻ ghi nợ ảo có phí phát hành hay thường niên không?", "Không. Thẻ ghi nợ ảo được miễn cả phí phát hành và phí thường niên."),
    ("fees_and_cards.txt", "Rút tiền mặt bằng thẻ ghi nợ tại ATM MauBank miễn phí.", "Rút tiền ở ATM của MauBank có mất phí không?", "Không mất phí."),
    ("fees_and_cards.txt", "Rút tiền tại ATM ngân hàng khác trong nước có phí 3.000 đồng mỗi giao dịch.", "Phí rút tiền tại ATM ngân hàng khác trong nước là bao nhiêu?", "3.000 đồng mỗi giao dịch."),
    ("fees_and_cards.txt", "Hạn mức rút tiền tại ATM là 20.000.000 đồng mỗi ngày.", "Mỗi ngày có thể rút tối đa bao nhiêu tiền tại ATM?", "20.000.000 đồng mỗi ngày."),
    ("fees_and_cards.txt", "Có thể yêu cầu tra soát trong vòng 60 ngày kể từ ngày phát sinh giao dịch.", "Có thể yêu cầu tra soát giao dịch trong bao lâu?", "Trong vòng 60 ngày kể từ ngày giao dịch phát sinh."),
    ("fees_and_cards.txt", "Ngân hàng Mau phản hồi kết quả tra soát trong tối đa 7 ngày làm việc.", "Thời gian phản hồi tra soát tối đa là bao lâu?", "Tối đa 7 ngày làm việc."),
    ("savings_and_deposits.txt", "Khách hàng có tài khoản thanh toán MauBank có thể mở tiết kiệm trực tuyến.", "Điều kiện để mở tiết kiệm trực tuyến là gì?", "Cần có tài khoản thanh toán MauBank."),
]

MULTI_HOP = [
    ("Chuyển nội bộ miễn phí và hoạt động liên tục ra sao?", "Chuyển tiền giữa hai tài khoản MauBank trên ứng dụng miễn phí và hoạt động 24/7.", ["digital_banking.txt"]),
    ("Tính phí cho hai giao dịch liên ngân hàng: 1 triệu đồng và 3 triệu đồng.", "Giao dịch 1 triệu đồng phí 1.000 đồng; giao dịch 3 triệu đồng phí 0,03% tức 900 đồng.", ["digital_banking.txt"]),
    ("Khách hàng chuyển 100 triệu đồng liên ngân hàng; hạn mức và phí tối đa có thể áp dụng thế nào?", "Hạn mức mặc định là 100 triệu đồng mỗi ngày; phí từ ngưỡng 2 triệu là 0,03%, tối đa 25.000 đồng.", ["digital_banking.txt"]),
    ("Muốn tăng hạn mức chuyển tiền cần làm gì và xác minh ra sao?", "Yêu cầu điều chỉnh tại quầy sau khi xác minh danh tính.", ["digital_banking.txt"]),
    ("Thanh toán hóa đơn miễn phí có thể thực hiện trong khung giờ nào?", "Không thu phí dịch vụ; thực hiện hàng ngày từ 00:00 đến 23:00.", ["digital_banking.txt"]),
    ("Đăng ký cần độ tuổi nào, giấy tờ gì và số điện thoại được dùng cho mấy tài khoản?", "Từ 18 tuổi, cần căn cước còn hiệu lực và số điện thoại đang dùng; mỗi số điện thoại chỉ đăng ký một tài khoản.", ["digital_banking.txt"]),
    ("Hỗ trợ hoạt động khi nào và mục tiêu phản hồi là bao lâu?", "Hỗ trợ trên ứng dụng 24/7; phản hồi mục tiêu trong một ngày làm việc.", ["digital_banking.txt"]),
    ("So sánh phí duy trì tài khoản với số dư tối thiểu.", "Phí duy trì là 0 đồng/tháng và số dư tối thiểu cũng là 0 đồng.", ["fees_and_cards.txt"]),
    ("Tổng phí năm đầu của thẻ vật lý lần đầu, gồm phát hành và thường niên, là bao nhiêu?", "50.000 đồng phí phát hành cộng 60.000 đồng thường niên, tổng cộng 110.000 đồng.", ["fees_and_cards.txt"]),
    ("So sánh phí năm đầu thẻ ghi nợ ảo với thẻ vật lý mới.", "Thẻ ảo không có phí phát hành hay thường niên; thẻ vật lý có phí phát hành 50.000 đồng và thường niên 60.000 đồng.", ["fees_and_cards.txt"]),
    ("So sánh phí rút 1 lần ở ATM MauBank và ngân hàng khác.", "ATM MauBank miễn phí; ATM ngân hàng khác trong nước thu 3.000 đồng/giao dịch.", ["fees_and_cards.txt"]),
    ("Mất thẻ ghi nợ thì phí cấp lại và thời hạn tra soát giao dịch là bao lâu?", "Cấp lại thẻ mất phí 30.000 đồng; yêu cầu tra soát trong 60 ngày từ ngày giao dịch.", ["fees_and_cards.txt"]),
    ("Hạn mức và phí rút tiền ATM mỗi ngày là gì?", "Hạn mức 20.000.000 đồng mỗi ngày; phí ATM MauBank miễn phí, ATM ngân hàng khác trong nước 3.000 đồng/giao dịch.", ["fees_and_cards.txt"]),
    ("Mở tiết kiệm trực tuyến cần điều kiện gì và số tiền tối thiểu bao nhiêu?", "Cần tài khoản thanh toán MauBank; số tiền mở tối thiểu 1.000.000 đồng.", ["savings_and_deposits.txt"]),
    ("Những kỳ hạn tiết kiệm trực tuyến nào có sẵn?", "1, 3, 6 và 12 tháng.", ["savings_and_deposits.txt"]),
    ("Nếu tất toán sớm, lãi suất nào áp dụng và có được rút trước hạn không?", "Được tất toán trước hạn; toàn bộ số tiền tất toán áp dụng lãi suất không kỳ hạn tại ngày tất toán.", ["savings_and_deposits.txt"]),
    ("Khi đến hạn có thể nhận tiền vào đâu hoặc tái tục thế nào?", "Có thể tất toán vào tài khoản thanh toán hoặc tự động tái tục cả gốc và lãi cho kỳ hạn tương ứng tiếp theo.", ["savings_and_deposits.txt"]),
    ("Có thể thay đổi lựa chọn tái tục vào lúc nào?", "Có thể thay đổi trên ứng dụng trước ngày đáo hạn.", ["savings_and_deposits.txt"]),
    ("Kết hợp mức phí thẻ vật lý và phí rút tại ATM khác ngân hàng.", "Phát hành thẻ vật lý lần đầu 50.000 đồng; rút tại ATM ngân hàng khác trong nước 3.000 đồng/giao dịch.", ["fees_and_cards.txt"]),
    ("So sánh phí duy trì tài khoản và phí thường niên thẻ ghi nợ.", "Tài khoản không mất phí duy trì; thẻ ghi nợ có phí thường niên 60.000 đồng/năm.", ["fees_and_cards.txt"]),
    ("Nếu đề nghị tra soát ngay sau giao dịch, thời gian khiếu nại còn bao lâu và phản hồi tối đa?", "Có thể yêu cầu trong vòng 60 ngày; phản hồi tối đa 7 ngày làm việc.", ["fees_and_cards.txt"]),
    ("Chuyển tiền nội bộ và chuyển khoản liên ngân hàng có cùng phí không?", "Không. Nội bộ miễn phí; liên ngân hàng dưới 2 triệu phí 1.000 đồng, từ 2 triệu phí 0,03% tối đa 25.000 đồng.", ["digital_banking.txt"]),
    ("Nêu hạn mức chuyển tiền và hạn mức rút ATM mỗi ngày.", "Chuyển tiền mặc định 100.000.000 đồng/ngày; rút ATM tối đa 20.000.000 đồng/ngày.", ["digital_banking.txt", "fees_and_cards.txt"]),
    ("Điều gì xảy ra khi tất toán sớm và lựa chọn đáo hạn tự động gồm những gì?", "Tất toán sớm áp dụng lãi suất không kỳ hạn; đến hạn có thể tái tục cả gốc và lãi cho kỳ hạn tiếp theo.", ["savings_and_deposits.txt"]),
    ("Có thể thanh toán hóa đơn và chuyển tiền nội bộ vào ban đêm không?", "Chuyển nội bộ hoạt động 24/7; thanh toán hóa đơn được thực hiện hàng ngày từ 00:00 đến 23:00.", ["digital_banking.txt"]),
]

UNANSWERABLE = [
    "Lãi suất vay mua nhà cố định trong 20 năm là bao nhiêu?",
    "Ngân hàng có chi nhánh nào tại Đà Nẵng?",
    "Phí chuyển tiền quốc tế bằng USD là bao nhiêu?",
    "Thẻ tín dụng được hoàn tiền bao nhiêu phần trăm?",
    "Tỷ giá USD hôm nay là bao nhiêu?",
    "Điều kiện vay mua ô tô gồm những gì?",
    "Ngân hàng có bảo hiểm tiền gửi tối đa bao nhiêu?",
    "Phí chuyển tiền SWIFT đến Nhật Bản thế nào?",
    "Ứng dụng hỗ trợ Apple Pay không?",
    "Lãi suất tiết kiệm kỳ hạn 18 tháng là bao nhiêu?",
    "Khách hàng doanh nghiệp mở tài khoản cần hồ sơ gì?",
    "Có thể đăng ký khoản vay trực tuyến tối đa bao nhiêu?",
    "Thời gian phê duyệt thẻ tín dụng mất mấy ngày?",
    "ATM ở địa chỉ cụ thể nào tại Thành phố Hồ Chí Minh?",
    "Ngân hàng có cung cấp dịch vụ két an toàn không?",
    "Phí thanh toán học phí tại trường đại học cụ thể là bao nhiêu?",
    "Tôi có thể vay tín chấp với lãi suất nào?",
    "Mức bồi thường bảo hiểm sức khỏe là bao nhiêu?",
    "Giao dịch chứng khoán có mất phí gì?",
    "Ngân hàng có hỗ trợ thanh toán QR ở nước ngoài không?",
    "Lãi suất không kỳ hạn chính xác hiện nay là bao nhiêu?",
    "Tổng đài điện thoại chăm sóc khách hàng là số nào?",
    "Thời gian làm việc tại quầy vào thứ Bảy thế nào?",
    "Phí chuyển tiền qua SWIFT bằng EUR là bao nhiêu?",
    "Hạn mức thanh toán thẻ tín dụng mỗi ngày là bao nhiêu?",
]


def main() -> None:
    cases = []
    for index, (filename, fact, question_a, question_b) in enumerate(FACTS, start=1):
        for question in (question_a, question_b):
            cases.append(
                {
                    "id": f"direct-{len(cases) + 1:03d}",
                    "category": "direct",
                    "question": question,
                    "reference_answer": fact,
                    "relevant_documents": [filename],
                }
            )
    for index, (question, answer, docs) in enumerate(MULTI_HOP, start=1):
        cases.append(
            {
                "id": f"multi-{index:03d}",
                "category": "multi_hop",
                "question": question,
                "reference_answer": answer,
                "relevant_documents": docs,
            }
        )
    for index, question in enumerate(UNANSWERABLE, start=1):
        cases.append(
            {
                "id": f"unknown-{index:03d}",
                "category": "unanswerable",
                "question": question,
                "reference_answer": None,
                "relevant_documents": [],
            }
        )
    if len(cases) != 100:
        raise ValueError(f"Expected 100 questions, generated {len(cases)}")
    OUTPUT.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
