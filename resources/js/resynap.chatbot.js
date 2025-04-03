var currentProfile = { };

window.leoBotUI = false;
window.leoBotContext = false;
function getBotUI() {
  if (window.leoBotUI === false) {
    window.leoBotUI = new BotUI("chatbot_container");
  }
  return window.leoBotUI;
}

function isMobile() {
  return navigator.userAgent.match(/Mobi|Android|iPhone|iPad|iPod/i) !== null;
}

function isEmailValid(email) {
  if (typeof email !== 'string') {
    return false; // Handle non-string inputs
  }

  const trimmedEmail = email.trim();

  if (!trimmedEmail) {
    return false; // Handle empty or whitespace-only strings
  }

  const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  return regex.test(trimmedEmail);
}

window.nodeIdChatSession = "chat_sessions_in_pc";
if (isMobile()) {
  console.log("User is on a mobile device");
  window.nodeIdChatSession = "chat_sessions_in_mb";
} else {
  console.log("User is on a PC");
}

function setActiveChatSession(id) {
  var node = $("#" + window.nodeIdChatSession);
  node.find("a").removeClass("active");
  node.find("#" + id).addClass("active");
}

function loadSelectedChatSession(node) {
  var sessionId = $(node).attr("id");
  setActiveChatSession(sessionId);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function loadChatSession(context, visitorId, okCallback) {
  window.leoBotContext = context;
  window.currentProfile.visitorId = visitorId;
  window.leoBotUI = new BotUI("chatbot_container");

  var url =
    BASE_URL_GET_VISITOR_INFO +
    "?visitor_id=" +
    visitorId +
    "&_=" +
    new Date().getTime();
  $.getJSON(url, function (data) {
    var e = data.error_code;
    var a = data.answer;
    console.log(data);
    if (e === 0) {
      var n = currentProfile.displayName;
      n = a.length > 0 ? a : n;
      currentProfile.displayName = n;
      newChatbotSession(currentProfile.displayName);
    } else if (e === 404) {
      askForContactInfo(visitorId);
    } else {
      chatbotShowError(a);
    }
  });

  if (typeof okCallback === "function") {
    okCallback();
  }
}

var newChatbotSession = function () {
  getBotUI().message.removeAll();
  if(window.sayHelloToUser){
    window.sayHelloToUser();
  }
};

var leoBotPromptQuestion = function (delay) {
  getBotUI()
    .action.text({
      delay: typeof delay === "number" ? delay : 800,
      action: {
        icon: "question-circle",
        cssClass: "chatbot-question-input",
        value: "", // show the prevous answer if any
        placeholder: "Give me a question",
      },
    })
    .then(function (res) {
      sendMessageToAgent("ask", res.value);
    });
};

var leoBotShowAnswer = function (answerInHtml, delay) {
  getBotUI()
    .message.add({
      human: false,
      cssClass: "chatbot_answer",
      content: answerInHtml,
      type: "html",
    })
    .then(function () {
      // format all href nodes in answer
      $("div.botui-message")
        .find("a")
        .each(function () {
          $(this).attr("target", "_blank");
          var href = $(this).attr("href");
          if (href.indexOf("google.com") < 0) {
            var q = encodeURIComponent($(this).text());
            href = "https://www.google.com/search?q=" + q;
          }
          $(this).attr("href", href);
        });
    });
};

var chatbotShowError = function (error, nextAction) {
  getBotUI()
    .message.add({
      human: false,
      cssClass: "chatbot-error",
      content: error,
      type: "html",
    })
    .then(nextAction || function () {});
};



var askTheEmailOfUser = function (name) {
  getBotUI()
    .action.text({
      delay: 0,
      action: {
        icon: "envelope-o",
        cssClass: "chatbot-question-input",
        value: "",
        placeholder: "Input your email here",
      },
    })
    .then(function (res) {
      var email = res.value;
      if (isEmailValid(email)) {
        console.log(name, email);
        var profileData = {
          loginProvider: "leochatbot",
          firstName: name,
          email: email,
        };
        if (window.CDP_TRACKING === true) {
          LeoObserverProxy.updateProfileBySession(profileData);
        }

        var a =
          "Hi " +
          name +
          ", system is creating a new account for you. Please wait for 5 seconds...";
        leoBotShowAnswer(a, 5000);
      } else {
        chatbotShowError(email + " is not a valid email", function () {
          askTheEmailOfUser(name);
        });
      }
    });
};

var askTheNameOfUser = function () {
  getBotUI()
    .action.text({
      delay: 0,
      action: {
        icon: "user-circle-o",
        cssClass: "chatbot-question-input",
        value: "",
        placeholder: "Input your name here",
      },
    })
    .then(function (res) {
      askTheEmailOfUser(res.value);
    });
};

var askForContactInfo = function (visitor_id) {
  var msg = "Hi friend, please enter your name and email to register new user";
  getBotUI()
    .message.add({
      human: false,
      cssClass: "leobot-question",
      content: msg,
      type: "html",
    })
    .then(askTheNameOfUser);
};

var sendMessageToAgent = function (context, question) {
  if (question.length > 1 && question !== "exit") {
    var processAnswer = function (answer) {
      if ("ask" === context) {
        leoBotShowAnswer(answer);
      }
      // save event into CDP
      if (typeof LeoObserver === "object" && CDP_TRACKING === true) {
        var sAnswer = answer.slice(0, 1000);
        var eventData = { question: question, answer: sAnswer };
        LeoObserver.recordEventAskQuestion(eventData);
      } else {
        console.log("SKIP LeoObserver.recordEventAskQuestion");
      }
    };

    var callServer = function (index) {
      var serverCallback = function (data) {
        getBotUI().message.remove(index);
        var error_code = data.error_code;
        var answer = data.answer;
        if (error_code === 0) {
          currentProfile.displayName = data.name;
          processAnswer(answer);
        } else if (error_code === 404) {
          askForContactInfo();
        } else {
          chatbotShowError(answer);
        }
      };

      var payload = {'private_mode':window.inPrivateMode};

      payload["question"] = question;
      payload["visitor_id"] = currentProfile.visitorId;
      payload["persona_name"] = $("#selected_agent_name").text().trim();
      payload["answer_in_format"] = "text";
      // TODO 

      callPostApi(BASE_URL_API, payload, serverCallback);
    };
    showChatBotLoader().then(callServer);
  }
};

var showChatBotLoader = function () {
  return getBotUI().message.add({ loading: true, content: "" });
};

var showChatMessage = function (msg, callback) {
  getBotUI()
    .message.add({
      human: true,
      cssClass: "chatbot-info",
      content: msg,
    })
    .then(function () {
      if (typeof callback === "function") callback();
    });
};

var callPostApi = function (urlStr, data, okCallback, errorCallback) {
  $.ajax({
    url: urlStr,
    crossDomain: true,
    data: JSON.stringify(data),
    contentType: "application/json",
    type: "POST",
    error: function (jqXHR, exception) {
      console.error("WE GET AN ERROR AT URL:" + urlStr);
      console.error(exception);
      if (typeof errorCallback === "function") {
        errorCallback();
      }
    },
  }).done(function (json) {
    okCallback(json);
    console.log("callPostApi", urlStr, data, json);
  });
};

var startChatbot = function (visitorId) {
  currentProfile.visitorId = visitorId;
  $("#chatbot_container_loader").hide();
  $("#chatbot_container").show();
  loadChatSession("leobot_website", visitorId);
};

function sendToChatbot() {
  var msg = $("#chatbot_input").val().trim();
  if (msg.length > 0) {
    sendMessageToAgent("ask", msg);
    showChatMessage(msg);    
  }
  $("#chatbot_input").val("");
}

function setupChatbotDone() {

  // the button handler
  $("#chatbot_input").keydown(function (event) {
      if ((event.key === "Enter" || event.keyCode === 13) && !event.shiftKey && !event.ctrlKey) {
          event.preventDefault(); // Prevent default newline behavior in textareas
          sendToChatbot();
      }
  });

  // 
  $("#persona_agent_list").change(function(){
    var selected = $(this).find("option:selected");
    $('#selected_agent_name').text(selected.text());
    $('#selected_agent_avatar_url').attr( 'src', selected.data('avatar'));
    
  })
}

// ready to load tracking script for long-term memory
$(document).ready(function () {
  var obsjs = location.protocol + "//" + CHATBOT_HOSTNAME + "/resources/js/leocdp.observer.js";
  if (CDP_TRACKING) {
    $.getScript(obsjs);
  } else {
    window.startChatbot("local_dev");
    currentProfile.visitorId = "0";
  }

  setupChatbotDone()
});