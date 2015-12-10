if (settings.addIngredientsLogic) {
$(function() {
  // SETTINGS
  var maxIngredients = 20;
  var mainUl = $('form.recipe ul.ingredients');
  var arTemplate = 'add_remove_tpl';
  var fixFinder = {'id': 'f_ingr__\\d+__(\\w+)', 'for': 'f_ingr__\\d+__(\\w+)', 'name': 'ingr\\.\\d+\\.(\\w+)'};
  var fixReplacer = {'id': 'f_ingr__%s__%s', 'for': 'f_ingr__%s__%s', 'name': 'ingr.%s.%s'};
  /////////////////
  var addRowHtml;

  var _fixHelper = function(field, attr, i) {
    var curAttrMatch = new RegExp(fixFinder[attr]).exec(field.attr(attr));
    field.attr(attr, myLib.sprintf(fixReplacer[attr], i, curAttrMatch[1]));
  };

  // Napraw identyfikatory
  var fixIdsAndNames = function() {
    mainUl.find('li').each(function(i) {
      $(this).find('label[for^=f_ingr__]').each(function(){_fixHelper($(this), 'for', i)});
      $(this).find('input[id^=f_ingr__]').each(function(){_fixHelper($(this), 'id', i)});
      $(this).find('input[name^=ingr]').each(function(){_fixHelper($(this), 'name', i)});
      $(this).find('select[id^=f_ingr__]').each(function(){_fixHelper($(this), 'id', i)});
      $(this).find('select[name^=ingr]').each(function(){_fixHelper($(this), 'name', i)});
    });
  };

  // Kliknięcie dodania
  var addHandler = function() {
    var newRow = addRowHtml.clone();
    $("input[id$=__portion]", newRow).numeric({allow:",."});
    addRecipeAutocompleteTo($("input[id$=__product]", newRow));
    $(this).parent().parent().parent().parent().append(newRow);
    fixIdsAndNames();
    redoButtons();
  };

  // Kliknięcie usunięcia
  var removeHandler = function() {
    $(this).parent().parent().parent().remove();
    fixIdsAndNames();
    redoButtons();
  };
  
  var upHandler = function() {
    var prev = $(this).parent().parent().parent().prev(), curr = $(this).parent().parent().parent();
    var tmp = [$('input[id$=__product]', prev).val(), $('input[id$=__portion]', prev).val(), $('select[id$=__weight]', prev).val()];
    $('input[id$=__product]', prev).val($('input[id$=__product]', curr).val());
    $('input[id$=__portion]', prev).val($('input[id$=__portion]', curr).val());
    $('select[id$=__weight]', prev).val($('select[id$=__weight]', curr).val());
    $('input[id$=__product]', curr).val(tmp[0]);
    $('input[id$=__portion]', curr).val(tmp[1]);
    $('select[id$=__weight]', curr).val(tmp[2]);
  };
  
  var downHandler = function() {
    var next = $(this).parent().parent().parent().next(), curr = $(this).parent().parent().parent();
    var tmp = [$('input[id$=__product]', next).val(), $('input[id$=__portion]', next).val(), $('select[id$=__weight]', next).val()];
    $('input[id$=__product]', next).val($('input[id$=__product]', curr).val());
    $('input[id$=__portion]', next).val($('input[id$=__portion]', curr).val());
    $('select[id$=__weight]', next).val($('select[id$=__weight]', curr).val());
    $('input[id$=__product]', curr).val(tmp[0]);
    $('input[id$=__portion]', curr).val(tmp[1]);
    $('select[id$=__weight]', curr).val(tmp[2]);
  };

  // Przegeneruj przyciski
  var redoButtons = function() {
    // Usuń wszystkie przyciski
    var innerDl = mainUl.find('li dl');
    innerDl.find('.ingr_add_remove').remove();
    var dlCount = innerDl.length;

    // Dodaj przyciski
    innerDl.each(function() {
      var ar = {'add': true, 'remove': true, 'up': true, 'down': true};
      var $this = $(this);
      
      if ($this.parent().prev().length == 0 && dlCount == 1) {
        ar.remove = false;
      }
      
      if (($this.parent().next().length == 0 && dlCount == maxIngredients) || $this.parent().next().length) {
        ar.add = false;
      }
      
      if ($this.parent().prev().length == 0) {
        ar.up = false;
      }
      
      if ($this.parent().next().length == 0) {
        ar.down = false;
      }
      
      var html = $(myLib.render(arTemplate, ar));
      html.find('a.add').click(addHandler);
      html.find('a.delete').click(removeHandler);
      html.find('a.arrow-up').click(upHandler);
      html.find('a.arrow-down').click(downHandler);
      $(this).append(html);
      
    });
  };
  
  var addRecipeAutocompleteTo = function(elems) {
      elems.autocomplete('/przepisy/autocomplete/product', {
        //mustMatch: true,
        minChars: 2,
        matchContains: "word",
        max: 50,
        delay: 600
    });
  };
  
  //INIT
  addRowHtml = mainUl.find('li:last').clone();
  addRowHtml.find('input').val('').end().find('select').val('g');
  mainUl.find('li:gt(0):last').remove();
  $("form.recipe #f_ig").numeric();
  $("form.recipe .ingredients input[id$=__portion]").numeric({allow:"."}); 
  redoButtons();
  
  $('<a class="preview_btn icon preview clearfix" title="Podgląd"></a>').click(function() {
    myLib.openWindowWithPost('/przepisy/podglad', 'preview', 'width=770,height=500,menubar=no,location=no,resizable=yes,scrollbars=yes,status=yes', {recipe: $('#f_recipe').val()});
  }).insertAfter('#f_recipe');

  addRecipeAutocompleteTo($("input[id$=__product]", mainUl));
  
  $('#f_tags').autocomplete('/przepisy/autocomplete/tag', {
        multiple: true,
        //mustMatch: true,
        minChars: 2,
        autoFill: true,
        max: 50,
        delay: 600
  });
});
};

if (settings.recipeFavsKey) {
$(function() {
  $('#add_to_favs_btn').click(function(){
    var $this = $(this);
    if ($this.hasClass('star_inactive')) {
      $.post('/przepisy/ulubione/dodaj/' + settings.recipeFavsKey, {}, function() {
        $this.addClass('star_active').removeClass('star_inactive');
      });
    } else {
      $.post('/przepisy/ulubione/usun/' + settings.recipeFavsKey, {}, function() {
        $this.addClass('star_inactive').removeClass('star_active');
      });      
    }
  });
});
};

if (settings.removeDisableButtons) {
$(function() {
  $('a.remove_alert').live('click', function(){
    if (confirm('Czy naprawdę chcesz usunąć przepis?\n\nPamiętaj, że operacja jest nieodwracalna!')) {
      $.post($(this).attr('href'), {}, function (data, textStatus) {
        window.location = data.redirectUrl;
      }, 'json');
    }
    return false;
  });
  $('a.disable_alert').live('click', function(){
    if (confirm('Czy naprawdę chcesz wyłączyć przepis?')) {
      $.post($(this).attr('href'), {}, function (data, textStatus) {
        window.location = data.redirectUrl;
      }, 'json');
    }
    return false;
  });
  $('a.enable_alert').live('click', function(){
    if (confirm('Czy naprawdę chcesz włączyć przepis?')) {
      $.post($(this).attr('href'), {}, function (data, textStatus) {
        window.location = data.redirectUrl;
      }, 'json');
    }
    return false;
  });
});
};

$(function() {
  var active = false;
  $('td.paging_next.use_xhr a, td.paging_prev.use_xhr a a').live('click', function(){
    if (active) {
      return false;
    }
    
    active = true;
    var $this_table = $(this).parents('table.xhr_targer'), url = $(this).attr('href');
    $this_table.addClass('loading').fadeTo('fast', 0.5, function(){
      $this_table.load(url + ' table>*', function(responseText, textStatus, XMLHttpRequest) {
        $this_table.removeClass('loading').fadeTo('fast', 1, function() { $(this).removeAttr('style')});
        active = false;
      });
    });
    return false;
  });
});
