(function ($) {
  "use strict";

  // Back to top button
  $(window).scroll(function() {
    if ($(this).scrollTop() > 100) {
      $('.back-to-top').fadeIn('slow');
    } else {
      $('.back-to-top').fadeOut('slow');
    }
  });
  $('.back-to-top').click(function(){
    $('html, body').animate({scrollTop : 0}, 1500, 'easeInOutExpo');
    return false;
  });

  // Initiate the wowjs animation library
  new WOW().init();

  // Initiate superfish on nav menu
  $('.nav-menu').superfish({
    animation: {
      opacity: 'show'
    },
    speed: 400
  });

  // Header scroll class
  $(window).scroll(function() {
    if ($(this).scrollTop() > 50) {
      $('#header').addClass('header-scrolled');
    } else {
      $('#header').removeClass('header-scrolled');
    }
  });

  if ($(window).scrollTop() > 100) {
    $('#header').addClass('header-scrolled');
  }

  // Smooth scroll
  $('.nav-menu a, .scrollto').on('click', function() {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var target = $(this.hash);
      if (target.length) {
        var top_space = 0;

        if ($('#header').length) {
          top_space = $('#header').outerHeight();

          if (! $('#header').hasClass('header-scrolled')) {
            top_space = top_space - 20;
          }
        }
        
        if ($(this).text() == 'Контакти') {
          $('html, body').animate({
            scrollTop: target.offset().top - top_space
          }, 1500, 'easeInOutExpo');
        } else {
          $('html, body').animate({
            scrollTop: target.offset().top - top_space - 60
          }, 1500, 'easeInOutExpo');
        }

        if ($(this).parents('.nav-menu').length) {
          $('.nav-menu .menu-active').removeClass('menu-active');
          $(this).closest('li').addClass('menu-active');
        }

        return false;
      }
    }
  });

  // Navigation
  var nav_sections = $('section');
  var main_nav = $('.nav-menu');
  var main_nav_height = $('#header').outerHeight();

  $(window).on('scroll', function () {
    var cur_pos = $(this).scrollTop();
  
    nav_sections.each(function() {
      var top = $(this).offset().top - main_nav_height,
          bottom = top + $(this).outerHeight();
  
      if (cur_pos >= top && cur_pos <= bottom) {
        main_nav.find('li').removeClass('menu-active menu-item-active');
        main_nav.find('a[href="#'+$(this).attr('id')+'"]').parent('li').addClass('menu-active menu-item-active');
      }
    });
  });

  // Rating

  $(".star").on("click", function() {
    for (let i = 1; i <= 5; ++i) {
      let id = '#star-' + i;
      $(id).css({
        "color": "rgb(0, 0, 0)",
        "-webkit-text-stroke": "0"
      });
    }
    let number = parseInt($(this).attr("id")[5]);
    $("#rating").attr("value", number);
    for (let i = 1; i <= number; ++i) {
      let id = '#star-' + i;
      $(id).css({
        "color": "rgb(248, 252, 21)",
        "-webkit-text-stroke": "1px #000"
      });
    }
  });

  // Inputs
  
})(jQuery);
