$(document).ready(function() {
	$("#messageArea").on("submit", function(event) {
		event.preventDefault();

		const date = new Date();
		const strTime = date.getHours() + ":" + date.getMinutes();
		const rawText = $("#text").val();
		const apiBaseUrl = (window.CHATBOT_API_BASE_URL || window.location.origin).replace(/\/+$/, "");

		const userHtml = '<div class="d-flex justify-content-end mb-4"><div class="msg_cotainer_send">' +
			rawText + '<span class="msg_time_send">' + strTime + '</span></div>' +
			'<div class="img_cont_msg"><img src="https://i.ibb.co/d5b84Xw/Untitled-design.png" ' +
			'class="rounded-circle user_img_msg"></div></div>';

		$("#text").val("");
		$("#messageFormeight").append(userHtml);

		$.ajax({
			data: { msg: rawText },
			type: "POST",
			url: apiBaseUrl + "/get"
		}).done(function(data) {
			const botHtml = '<div class="d-flex justify-content-start mb-4">' +
				'<div class="img_cont_msg"><img src="https://cdn-icons-png.flaticon.com/512/387/387569.png" ' +
				'class="rounded-circle user_img_msg"></div><div class="msg_cotainer">' + data +
				'<span class="msg_time">' + strTime + '</span></div></div>';
			$("#messageFormeight").append($.parseHTML(botHtml));
		}).fail(function() {
			const errorHtml = '<div class="d-flex justify-content-start mb-4">' +
				'<div class="msg_cotainer">Could not reach the chatbot service. Check the API URL and CORS configuration.</div></div>';
			$("#messageFormeight").append(errorHtml);
		});
	});
});
