$(document).ready(function () {
  setupMindmapController();

  $("#render-btn").click(function () {
    const mindmapInput = $("#mindmap-input").val();

    // call API to generate learning content
    const mindmapCode = $("#mindmap-code").val();
    renderMindmap(mindmapCode);
  });
});

var renderMindmap = function (mindmapCode) {
  console.log(mindmapCode);
  $("#mermaid-container").html(`<pre class="mermaid">${mindmapCode}</pre>`);
  mermaid.run();

  var video_src = "resources/generated_videos/generated_video_20250312_150209.mp4";
  $("#summary_video").attr("src", video_src).show()[0].play();
};

var setupMindmapController = function () {
  let scale = 1;

  $("#zoom-in").click(function () {
    scale += 0.1;
    $("#mermaid-container").css("transform", `scale(${scale})`);
  });

  $("#zoom-out").click(function () {
    scale = Math.max(0.5, scale - 0.1);
    $("#mermaid-container").css("transform", `scale(${scale})`);
  });

  $("#reset").click(function () {
    scale = 1;
    $("#mermaid-container").css("transform", `scale(${scale})`);
  });

  setTimeout(function () {
    $("#mermaid-container").show();
    const mindmapCode = $("#mindmap-code").val();
    renderMindmap(mindmapCode);
  }, 1000);
};
