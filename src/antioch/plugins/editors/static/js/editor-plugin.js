// Loaded in the client window automatically
(function($) {
  $('head').append($('<link>').attr({
    href:   "/assets/less/editors.less",
    type:   "text/css",
    media:  "screen",
    rel:    "stylesheet/less"
  }));
  less.sheets.push($('link[href="/assets/less/editors.less"]')[0]);
  less.refresh();
  
  var editorsPanel = $('<div>').attr({
    "class":   "editors-panel"
  });
  
  var tabList = $('<ul>').attr({
    "class":   "nav nav-tabs",
    "data-tabs": "tabs"
  });
  editorsPanel.append(tabList);
  
  var tabContent = $('<div>').attr({
    "class":   "tab-content"
  });
  editorsPanel.append(tabContent);
  
  $('.page-container').append(editorsPanel);
  
  $(document).antioch('addMessageListener', 'edit', function(msg){
    var tabContentId = "edit-tab-content-" + msg.details.kind.replace('/', '-') + '-' + msg.details.id;
    var tabId = "edit-tab-" + msg.details.kind.replace('/', '-') + '-' + msg.details.id;
    var closeTab = function(){
      $('#' + tabId).remove();
      $('#' + tabContentId).remove();
    };

    var newTabContent = $('<div>').attr({
      'id': tabContentId,
      'class': "tab-pane"
    });
    newTabContent.load('/editor/' + msg.details.kind + '/' + msg.details.id);
    
    var newTab = $('<a>').attr({
      'id': tabId,
      'href':  "#" + tabContentId,
      'data-toggle': "tab"
    }).html(msg.details.__str__);
    
    newTab.append($("<a>").attr({
      'class': 'close-tab glyphicon glyphicon-remove'
    }).click(closeTab));
    
    tabList.append($("<li>").append(newTab));
    tabContent.append(newTabContent);
    
    newTab.tab('show');
  });
})(jQuery);
