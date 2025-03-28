var currentUserProfile = { visitorId: "", displayName: "good friend" };

window.leoBotUI = false;
window.leoBotContext = false;
function getBotUI() {
  if (window.leoBotUI === false) {
    window.leoBotUI = new BotUI("chatbot_container");
  }
  return window.leoBotUI;
}

function initLeoChatBot(context, visitorId, okCallback) {
  window.leoBotContext = context;
  window.currentUserProfile.visitorId = visitorId;
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
      var n = currentUserProfile.displayName;
      n = a.length > 0 ? a : n;
      currentUserProfile.displayName = n;
      showLeoChatBot(currentUserProfile.displayName);
    } else if (e === 404) {
      askForContactInfo(visitorId);
    } else {
      leoBotShowError(a, leoBotPromptQuestion);
    }
  });

  if (typeof okCallback === "function") {
    okCallback();
  }
}

var showLeoChatBot = function (displayName) {
  var msg = "Hi " + displayName + ", you may ask me for anything";
  var msgObj = { content: msg, cssClass: "leobot-answer" };
  getBotUI().message.removeAll();
  getBotUI().message.bot(msgObj).then(leoBotPromptQuestion);
};

var leoBotPromptQuestion = function (delay) {
  getBotUI()
    .action.text({
      delay: typeof delay === "number" ? delay : 800,
      action: {
        icon: "question-circle",
        cssClass: "leobot-question-input",
        value: "", // show the prevous answer if any
        placeholder: "Give me a question",
      },
    })
    .then(function (res) {
      sendQuestionToLeoAI("ask", res.value);
    });
};

var leoBotShowAnswer = function (answerInHtml, delay) {
  getBotUI()
    .message.add({
      human: false,
      cssClass: "leobot-answer",
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

      delay =
        typeof delay === "number"
          ? delay
          : answerInHtml.length > 200
          ? 6000
          : 1800;
      leoBotPromptQuestion(delay);
    });
};

var leoBotShowError = function (error, nextAction) {
  getBotUI()
    .message.add({
      human: false,
      cssClass: "leobot-error",
      content: error,
      type: "html",
    })
    .then(nextAction || function () {});
};

function isEmailValid(email) {
  const regex =
    /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return regex.test(email);
}

var askTheEmailOfUser = function (name) {
  getBotUI()
    .action.text({
      delay: 0,
      action: {
        icon: "envelope-o",
        cssClass: "leobot-question-input",
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
        leoBotShowError(email + " is not a valid email", function () {
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
        cssClass: "leobot-question-input",
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

var sendQuestionToLeoAI = function (context, question) {
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
          currentUserProfile.displayName = data.name;
          processAnswer(answer);
        } else if (error_code === 404) {
          askForContactInfo();
        } else {
          leoBotShowError(answer, leoBotPromptQuestion);
        }
      };

      var payload = { prompt: question, question: question };
      payload["visitor_id"] = currentUserProfile.visitorId;
      payload["answer_in_language"] = $("#leobot_answer_in_language").val();
      payload["answer_in_format"] = "html";
      payload["context"] = "I am a smart chatbot with AI capabilities.";
      callPostApi(BASE_URL_LEOBOT, payload, serverCallback);
    };
    showChatBotLoader().then(callServer);
  }
};

var showChatBotLoader = function () {
  return getBotUI().message.add({ loading: true, content: "" });
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

var startLeoChatBot = function (visitorId) {
  currentUserProfile.visitorId = visitorId;
  $("#LEO_ChatBot_Container_Loader").hide();
  $("#chatbot_container, #leobot_answer_in_language").show();
  initLeoChatBot("leobot_website", visitorId);
};

$(document).ready(function () {
  // ready to load
  var obsjs = location.protocol + "//" + CHATBOT_HOSTNAME + "/resources/js/leocdp.observer.js";

  if (CDP_TRACKING) {
    $.getScript(obsjs);
  } else {
    window.startLeoChatBot("local_dev");
    currentUserProfile.visitorId = "0";
  }
});
