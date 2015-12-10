$(function() {
  // Handle ajax errors
  if ($('ul.flash').length == 0) {
    $('#no_js_info').after('<ul class="flash"></ul>');
  }
  
  $('ul.flash').append('<li id="ajax_error_flash" class="error" style="display: none;">Błąd komunikacji z serwerem! Spróbuj ponownie później lub sprawdź połączenie z internetem.</li>');
  
  $('#ajax_error_flash').ajaxError(function(event, request, settings) {
    $(this).show();
  });
  
  // Handle notifications closing
  $('ul.flash li').each(function() {
    $('<div class="close" title="Ukryj">x</div>').click(function(){$(this).parent().fadeOut('fast')}).appendTo($(this));
  });
  
  // Handle search box in header
  var sqInput = $('#main_search input:first');
  var defaultText = 'Wpisz frazę...';
  $('#main_search').submit(function() {
    if (sqInput.val().length < 3 || sqInput.val() == defaultText) {
      alert('Wyszukiwanie wymaga podania przynajmniej 3 znaków!');
      return false;
    }
  });
  $('#search_box').submit(function() {
    if ($('input[name=q]', this).val().length < 3) {
      alert('Wyszukiwanie wymaga podania przynajmniej 3 znaków!');
      return false;
    } else {
      /*
      $('#box_search_results').show();
      if ($('#box_search_results td.paging_next.use_xhr a').length == 0) {
        $('#box_search_results td.paging_next.use_xhr').append('<a href="#">&nbsp;</a>');
      }
      $('#box_search_results td.paging_next.use_xhr a').attr('href', $(this).attr('action') + '?' +$(this).serialize()).click();
      */
    }
  });  
  if (sqInput.val().length == 0) {
    sqInput.val(defaultText);
  }
  sqInput.focus(function() {
    if (sqInput.val() == defaultText) {
      sqInput.val('');
    }
  }).blur(function() {
    if (sqInput.val() == '') {
      sqInput.val(defaultText);
    }
  });
  
  // Handle advanced search switch
  $('#adv_switch').click(function() {
    var advHidden = $('#search_box input[name=a]');
    if (advHidden.val() == '0') {
      $('.adv_search_opt').show('fast');
      advHidden.val('1');
    } else {
      $('.adv_search_opt').hide('fast');
      advHidden.val('0');
    }
  });
  //var d = '@przepisymm.info';
  //$('a[href=^mailto]').replaceWith('<a href="mailto:info'+domain+'">info'+domain+'</a>');
  
});

// GFC settings, it should be last...
google.friendconnect.container.setParentUrl('/');

var gfcSkins = {};
gfcSkins.signIn = {
  BORDER_COLOR: 'transparent',
  ENDCAP_BG_COLOR: '#2B6488',
  ENDCAP_TEXT_COLOR: '#fff',
  ENDCAP_LINK_COLOR: '#ddd',
  ALTERNATE_BG_COLOR: '#dddddd',
  CONTENT_BG_COLOR: 'transparent',
  CONTENT_LINK_COLOR: '#ddd',
  CONTENT_TEXT_COLOR: '#fff',
  CONTENT_SECONDARY_LINK_COLOR: '#3C91C7',
  CONTENT_SECONDARY_TEXT_COLOR: '#ddd',
  CONTENT_HEADLINE_COLOR: '#fff',
  ALIGNMENT: 'right'
};
gfcSkins.members = {
  BORDER_COLOR: 'transparent',
  ENDCAP_BG_COLOR: 'transparent',
  ENDCAP_TEXT_COLOR: '#333333',
  ENDCAP_LINK_COLOR: '#2B6488',
  ALTERNATE_BG_COLOR: '#dddddd',
  CONTENT_BG_COLOR: 'transparent',
  CONTENT_LINK_COLOR: '#2B6488',
  CONTENT_TEXT_COLOR: '#333333',
  CONTENT_SECONDARY_LINK_COLOR: '#3C91C7',
  CONTENT_SECONDARY_TEXT_COLOR: '#555555',
  CONTENT_HEADLINE_COLOR: '#333333',
  NUMBER_ROWS: '3'
};

gfcSkins.review = {
  BORDER_COLOR: 'transparent',
  ENDCAP_BG_COLOR: 'transparent',
  ENDCAP_TEXT_COLOR: '#333333',
  ENDCAP_LINK_COLOR: '#2B6488',
  ALTERNATE_BG_COLOR: '#dddddd',
  CONTENT_BG_COLOR: 'transparent',
  CONTENT_LINK_COLOR: '#2B6488',
  CONTENT_TEXT_COLOR: '#333333',
  CONTENT_SECONDARY_LINK_COLOR: '#3C91C7',
  CONTENT_SECONDARY_TEXT_COLOR: '#555555',
  CONTENT_HEADLINE_COLOR: '#333333',
  DEFAULT_COMMENT_TEXT: '\u2013 dodaj tutaj swoj\u0105 recenzj\u0119 \u2013',
  HEADER_TEXT: 'Oceny',
  POSTS_PER_PAGE: '5'
};

gfcSkins.recommend_btn = {
  HEIGHT: '21',
  BUTTON_STYLE: 'compact',
  BUTTON_TEXT: 'Pole\u0107 innym!',
  BUTTON_ICON: 'default'
};

gfcSkins.recommend = {
  BORDER_COLOR: 'transparent',
  ENDCAP_BG_COLOR: 'transparent',
  ENDCAP_TEXT_COLOR: '#333333',
  ENDCAP_LINK_COLOR: '#2B6488',
  ALTERNATE_BG_COLOR: '#dddddd',
  CONTENT_BG_COLOR: 'transparent',
  CONTENT_LINK_COLOR: '#2B6488',
  CONTENT_TEXT_COLOR: '#333333',
  CONTENT_SECONDARY_LINK_COLOR: '#3C91C7',
  CONTENT_SECONDARY_TEXT_COLOR: '#555555',
  CONTENT_HEADLINE_COLOR: '#333333',
  HEADER_TEXT: 'Zobacz, co polecają inni...',
  RECOMMENDATIONS_PER_PAGE: '10'
};

gfcSkins.activity = {
  BORDER_COLOR: 'transparent',
  ENDCAP_BG_COLOR: 'transparent',
  ENDCAP_TEXT_COLOR: '#333333',
  ENDCAP_LINK_COLOR: '#2B6488',
  ALTERNATE_BG_COLOR: '#dddddd',
  CONTENT_BG_COLOR: 'transparent',
  CONTENT_LINK_COLOR: '#2B6488',
  CONTENT_TEXT_COLOR: '#333333',
  CONTENT_SECONDARY_LINK_COLOR: '#3C91C7',
  CONTENT_SECONDARY_TEXT_COLOR: '#555555',
  CONTENT_HEADLINE_COLOR: '#333333',
  HEIGHT: '240'
};

google.friendconnect.container.initOpenSocialApi({
  site: settings.gfcSiteId,
  onload: settings.gfcOnLoad || function(securityToken) {
    if (!window.gfcFirstTime) {
      window.gfcFirstTime = 1;
    } else {
      window.top.location.reload();
    }
  }
});

$(function() {  
  if ($('#gfc_login').length) {
    google.friendconnect.container.renderSignInGadget({id: 'gfc_login', site: settings.gfcSiteId}, gfcSkins.signIn);
  }
  
  if ($('#gfc_button').length) {
    google.friendconnect.renderSignInButton({ 'id': 'gfc_button', 'style': 'long', 'text': 'Zaloguj się używając Sieci Znajomych Google' });
  }
  
  if ($('#gfc_members').length) {
    google.friendconnect.container.renderMembersGadget({id: 'gfc_members', site: settings.gfcSiteId }, gfcSkins.members);
  }

  if ($('#gfc_review').length) {
    google.friendconnect.container.renderReviewGadget({ id: 'gfc_review', site: settings.gfcSiteId, 'view-params':{"disableMinMax":"true","scope":"PAGE","startMaximized":"true"}},gfcSkins.review);
  }

  if ($('#gfc_recommend_btn').length) {
    google.friendconnect.container.renderOpenSocialGadget({ id: 'gfc_recommend_btn', url:'http://www.google.com/friendconnect/gadgets/recommended_pages.xml', height: 21, site: settings.gfcSiteId, 'view-params':{"pageUrl":location.href,"pageTitle":(document.title ? document.title.replace(' - Przepisy diety Montignac', '') : location.href),"docId":"recommendedPages"}}, gfcSkins.recommend_btn);
  }
  
  if ($('#gfc_recommend').length) {
    google.friendconnect.container.renderOpenSocialGadget({ id: 'gfc_recommend', url:'http://www.google.com/friendconnect/gadgets/recommended_pages.xml', site: settings.gfcSiteId, 'view-params':{"docId":"recommendedPages"}}, gfcSkins.recommend);
  }
  
  if ($('#gfc_activity').length) {
    google.friendconnect.container.renderOpenSocialGadget({ id: 'gfc_activity', url:'http://www.google.com/friendconnect/gadgets/activities.xml', height: 240, site: settings.gfcSiteId, 'view-params':{"scope":"SITE"}}, gfcSkins.activity);
  }
});