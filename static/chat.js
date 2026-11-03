$(document).ready(function() {
	function appendMessage(text, isUser, time) {
		const $row = $("<div>").addClass(
			"d-flex mb-4 " + (isUser ? "justify-content-end" : "justify-content-start")
		);
		const $bubble = $("<div>").addClass(isUser ? "msg_cotainer_send" : "msg_cotainer");
		const $timestamp = $("<span>")
			.addClass(isUser ? "msg_time_send" : "msg_time")
			.text(time);

		$bubble.text(text).append($timestamp);
		const $avatar = $("<img>")
			.addClass("rounded-circle user_img_msg")
			.attr("alt", isUser ? "You" : "Medical chatbot")
			.attr(
				"src",
				isUser
					? "https://i.ibb.co/d5b84Xw/Untitled-design.png"
					: "https://cdn-icons-png.flaticon.com/512/387/387569.png"
			);
		$row.append(isUser ? $bubble : $("<div>").addClass("img_cont_msg").append($avatar));
		if (isUser) {
			$row.append($("<div>").addClass("img_cont_msg").append($avatar));
		}
		if (!isUser) {
			$row.append($bubble);
		}
		$("#messageFormeight").append($row);
	}

	$("#messageArea").on("submit", function(event) {
		event.preventDefault();

		const rawText = String($("#text").val() || "").trim();
		if (!rawText) {
			return;
		}

		const date = new Date();
		const strTime = date.getHours() + ":" + String(date.getMinutes()).padStart(2, "0");
		const apiBaseUrl = (window.CHATBOT_API_BASE_URL || window.location.origin).replace(/\/+$/, "");
		const $sendButton = $("#send").prop("disabled", true);
		const $textInput = $("#text").prop("disabled", true);

		appendMessage(rawText, true, strTime);
		$textInput.val("");

		$.ajax({
			data: { msg: rawText },
			type: "POST",
			url: apiBaseUrl + "/get"
		}).done(function(data) {
			appendMessage(String(data), false, strTime);
		}).fail(function(xhr) {
			const errorMessage = xhr.responseText || "Could not reach the chatbot service. Please try again later.";
			appendMessage(errorMessage, false, strTime);
		}).always(function() {
			$sendButton.prop("disabled", false);
			$textInput.prop("disabled", false).trigger("focus");
		});
	});
});
