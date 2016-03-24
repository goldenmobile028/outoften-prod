/***** Lightbox2 configuration *****/

lightbox.option({
	fadeDuration: 100,
	resizeDuration: 100
});

/***** Constants *****/

var usernameKey = "usernameKey";
var passwordKey = "passwordKey";
var timeoutDuration = 10000;


/***** API *****/

//var serverUrl = "https://outoften-prod.herokuapp.com";
var serverUrl = "../";
var apiBase = "/api/v1/";
var loginEndpoint = "admin/login/";
var flaggedListEndpoint = "admin/flagged_list/";
var submitModerationEndpoint = "admin/submit_moderation/";

var FLAG_APPROVED = 2;
var FLAG_BANNED = 3;

var CATEGORY_LANDSCAPE = 0;
var CATEGORY_SELFIE = 1;
var CATEGORY_RIDES = 2;
var CATEGORY_RANDOM = 3;

function generateLoginApiUrl() {
	return serverUrl + apiBase + loginEndpoint;
}

function generateFlaggedListApiUrl() {
	return serverUrl + apiBase + flaggedListEndpoint;
}

function generateSubmitModerationApiUrl() {
	return serverUrl + apiBase + submitModerationEndpoint;
}


/***** Credentials *****/

function getUsername() {
	return Cookies.get(usernameKey);
}

function setUsername(username) {
	Cookies.set(usernameKey, username, {
		expires: 2
	});
}

function unsetUsername() {
	Cookies.remove(usernameKey);
}

function getPassword() {
	return Cookies.get(passwordKey);
}

function setPassword(password) {
	Cookies.set(passwordKey, password, {
		expires: 2
	});
}

function unsetPassword() {
	Cookies.remove(passwordKey);
}

function clearCredentials() {
	unsetUsername();
	unsetPassword();
}


/***** Login page *****/

function setupLoginPage() {
	var wrongCredentialsMessage = "Username or password are incorrect. Please try again.";
	var insufficientCredentialsMessage = "Both username and password must be provided. Please try again.";
	var serverErrorMessage = "There was an issue with the server. Please check your internet connection and try again.";

	function postLoginRequest() {
		var username = $("#login_form .username").val();
		var password = $("#login_form .password").val();

		if (username.length > 0 &&
			password.length > 0) {
			$("#login_page .error_message").hide();
			$("#login_page .throbber-loader").show();
			$("#login_form :input").prop("disabled", true);

			function onRequestEnd() {
				$(".throbber-loader").hide();
				$("#login_form :input").prop("disabled", false);
			}

			var requestData = {
				username: username,
				password: password
			};

			$.ajax({
				url: generateLoginApiUrl(),
				type: "POST",
				dataType: "json",
				//crossDomain: true,
				timeout: timeoutDuration,
				data: JSON.stringify(requestData),
				success: function(data, textStatus) {
					onRequestEnd();

					status = data["status"];

					if (status !== undefined &&
						status !== "bad credentials") {
						setUsername(username);
						setPassword(password);
						openHash("#admin_panel");
						console.log("success");
					}
					else {
						$("#login_page .error_message").text(wrongCredentialsMessage);
						$("#login_page .error_message").show();
					}
				},
				error: function(xhr, textStatus, errorThrown) {
					onRequestEnd();

					$("#login_page .error_message").text(serverErrorMessage);
					$("#login_page .error_message").show();
				}
			});
		}
		else {
			$("#login_page .error_message").text(insufficientCredentialsMessage);
			$("#login_page .error_message").show();
		}
	}

	$("#login_form .submit_button").unbind("click").click( function() {
		postLoginRequest();
	});

	$("#login_form .username").keypress(function (e) {
  		if (e.which == 13) {
  			$("#login_form .password").focus();
  			return false;
  		}
  	});

  	$("#login_form .password").keypress(function (e) {
  		if (e.which == 13) {
  			postLoginRequest();
  			return false;
  		}
  	});
}

function renderLoginPage() {
	$("#login_form .username, #login_form .password").val("");
	$("#login_page").show();
};


/***** Admin panel page *****/

function logout() {
	clearCredentials();
	openHash("#login");
}

function isEven(n) {
   return n % 2 == 0;
}

function getCategoryTitle(n) {
	var category = "";

	if (n===CATEGORY_LANDSCAPE) {
		category = "Landscape";
	}
	else if (n===CATEGORY_SELFIE) {
		category = "Selfie";
	}
	else if (n===CATEGORY_RIDES) {
		category = "Rides";
	}
	else if (n===CATEGORY_RANDOM) {
		category = "Random";
	}
	else {
		category = "";
	}

	return category;
}

function submitModerationDecision(photoId, flag_status, $moderation_item) {
	$moderation_item.find(".throbber-loader").show();
	$moderation_item.find(".approve_button").prop("disabled", true);
	$moderation_item.find(".ban_button").prop("disabled", true);
	$moderation_item.find(".error_message").hide();

	var requestData = {
		username: getUsername(),
		password: getPassword(),
		photo_id: photoId,
		flag_status: flag_status
	};

	$.ajax({
		url: generateSubmitModerationApiUrl(),
		type: "POST",
		dataType: "json",
		//crossDomain: true,
		timeout: timeoutDuration,
		data: JSON.stringify(requestData),
		success: function(data, textStatus) {
			$moderation_item.attr("data-moderated", "1");

			$moderation_item.fadeTo(.3, .2);
			$moderation_item.find(".throbber-loader").hide();
			$moderation_item.find(".approve_button").hide();
			$moderation_item.find(".ban_button").hide();

			if (flag_status === FLAG_BANNED) {
				$moderation_item.find(".banned_message").show();
			}
			else if (flag_status === FLAG_APPROVED) {
				$moderation_item.find(".approved_message").show();
			}

			// if all items have been moderated
			if ($("#moderation_list .moderation_item").length === $(".moderation_item[data-moderated='1']").length) {
				getFlaggedList();	// get new items to moderate. this will empty out the current list, show the loader, and then fetch for us
			}
		},
		error: function(xhr, textStatus, errorThrown) {
			$moderation_item.find(".throbber-loader").hide();
			$moderation_item.find(".approve_button").prop("disabled", false);
			$moderation_item.find(".ban_button").prop("disabled", false);
			$moderation_item.find(".error_message").show();
		}
	});
}

function onGetFlaggedListSuccess(data) {
	$("#admin_panel .throbber-loader").hide();

	status = data["status"];

	if (status === "ok") {
		var photos = data["photos"];
		if (photos.length > 0) {
			$("#moderation_list").empty();
			for (var i=0; i<photos.length; i++) {
				var photo = photos[i];

				var moderation_item_class = "";
				if (isEven(i)) {
					moderation_item_class = "moderation_item white";
				}
				else {
					moderation_item_class = "moderation_item gray";
				}

				var photoUrl = photo["image_url"];
				var photoId = photo["photo_id"];
				var category = getCategoryTitle(photo["category"]);
				var inappropriateCount = photo["flag_count_inappropriate"];
				var miscategorizedCount = photo["flag_count_miscategorized"];
				var spamCount = photo["flag_count_spam"];

				$("	<div class='"+moderation_item_class+"' data-photo_id='"+photoId+"' data-moderated='0'> \
					<div class='moderation_thumb'> \
					<a href='"+photoUrl+"' data-lightbox='"+photoUrl+"' data-title='Photo'> \
					<img src='"+photoUrl+"'/> \
					</a> \
					</div> \
					<div class='moderation_item_details'> \
						<div class='category'> \
						Category: "+category+" \
						</div> \
						<div class='inappropriate_count'> \
						Inappropriate flag count: "+inappropriateCount+" \
						</div> \
						<div class='miscategorized_count'> \
						Miscategorized flag count: "+miscategorizedCount+" \
						</div> \
						<div class='spam_count'> \
						Spam flag count: "+spamCount+" \
						</div> \
						<div class='actions'> \
						<button type='button' class='approve_button'>Approve</button> \
						&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \
						<button type='button' class='ban_button'>&nbsp;&nbsp;&nbsp;&nbsp;Ban&nbsp;&nbsp;&nbsp;&nbsp;</button> \
						<div class='throbber-loader' style='clear:both;'></div> \
						<div class='error_message' style='color: #BC2C4C'>Error. Please try again.</div> \
						<div class='approved_message'>APPROVED</div> \
						<div class='banned_message'>BANNED</div> \
						</div> \
					</div> \
				</div>")
				.appendTo('#moderation_list');
			}

			$(".moderation_item_details .throbber-loader").hide();
			$(".moderation_item_details .approved_message").hide();
			$(".moderation_item_details .banned_message").hide();

			$(".moderation_item_details .error_message").hide();

			$(".moderation_item_details .ban_button").unbind("click").bind("click", function() {
				var photoId = $(this).closest(".moderation_item").data("photo_id");
				submitModerationDecision(photoId, FLAG_BANNED, $(this).closest(".moderation_item"));
			});

			$(".moderation_item_details .approve_button").unbind("click").bind("click", function() {
				var photoId = $(this).closest(".moderation_item").data("photo_id");
				submitModerationDecision(photoId, FLAG_APPROVED, $(this).closest(".moderation_item"));
			});
		}
		else {
			$("#moderation_list_empty").show();
		}
	}
	else {
		$.blockUI({ message: '<p>Your session has expired. You will now be logged out.</p>' });

		setTimeout(function() {
			$.unblockUI();
			logout();
		}, 1000);
	}
}

// for now, we technically have it as a post
function getFlaggedList() {
	$("#admin_panel .throbber-loader").show();
	$("#moderation_list_empty").hide();
	$("#moderation_list").empty();

	var requestData = {
			username: getUsername(),
			password: getPassword(),
		};

	$.ajax({
		url: generateFlaggedListApiUrl(),
		type: "POST",
		dataType: "json",
		//crossDomain: true,
		timeout: timeoutDuration,
		data: JSON.stringify(requestData),
		success: function(data, textStatus) {
			onGetFlaggedListSuccess(data);
		},
		error: function(xhr, textStatus, errorThrown) {
			console.log("Failed to load flagged list. Retrying...")
			getFlaggedList();
		}
	});
}

function setupAdminPanelPage() {
	$("#moderation_list_empty").hide();

	$("#admin_panel .menu-link-logout").unbind("click").click(function(event) {
		event.preventDefault();
		logout();
	});

	$(".refresh_moderation_list_button").unbind("click").click(function(event) {
		getFlaggedList();
	});
}

function renderAdminPanelPage() {
	$("#admin_panel").show();
	getFlaggedList();
};


/***** Error page *****/

function renderErrorPage() {
	$("#error_page").show();
};


/***** App logic *****/

function render(url) {
	$(".page").hide();
	$("p.error_message").hide();
	$(".page .throbber-loader").hide();

	var keyword = url.split('/')[0];

	var username = getUsername();
	var password = getPassword();

	var map = {
		"#login": function() {
			if (username !== undefined &&
				password !== undefined) {
				openHash("#admin_panel");
			}
			else {
				renderLoginPage();
			}
		},

		"#admin_panel": function() {
			if (username !== undefined &&
				password !== undefined) {
				renderAdminPanelPage();
			}
			else {
				openHash("#login");
			}
		},
	};

	var renderFunction = map[keyword];

	if (renderFunction !== undefined) {
		renderFunction();
	}
	else {
		if (username !== undefined &&
			password !== undefined) {
			openHash("#admin_panel");
		}
		else {
			openHash("#login");
		}
		//renderErrorPage();
	}
}

function onAppLoad() {
	$("#loading_content").fadeOut("slow").hide();
	$("#app_content").fadeIn("slow");

	$(".page").hide();

	var username = getUsername();
	var password = getPassword();

	$(window).bind("hashchange", function(e) {
		render(window.location.hash);
	});

	render(window.location.hash);
}

function openHash(hash) {
	window.location.hash = hash;
}

/***** Entry point *****/

$(document).ready(function() {
	setupLoginPage();
	setupAdminPanelPage();

	onAppLoad();
});
