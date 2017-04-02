(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['tweet'] = template({"1":function(container,depth0,helpers,partials,data) {
    var helper;

  return "      <img src="
    + container.escapeExpression(((helper = (helper = helpers.media || (depth0 != null ? depth0.media : depth0)) != null ? helper : helpers.helperMissing),(typeof helper === "function" ? helper.call(depth0 != null ? depth0 : {},{"name":"media","hash":{},"data":data}) : helper)))
    + ">\n";
},"compiler":[7,">= 4.0.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : {}, alias2=helpers.helperMissing, alias3="function", alias4=container.escapeExpression;

  return "<div class=\"tweet zero_box_red\">\n  <div class=\"tweet_pic\">\n    <image src="
    + alias4(((helper = (helper = helpers.profile_image || (depth0 != null ? depth0.profile_image : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"profile_image","hash":{},"data":data}) : helper)))
    + "> \n    <p class=\"username\"><b>"
    + alias4(((helper = (helper = helpers.user || (depth0 != null ? depth0.user : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"user","hash":{},"data":data}) : helper)))
    + "</b></p>\n    <p class=\"handle\">"
    + alias4(((helper = (helper = helpers.screen_name || (depth0 != null ? depth0.screen_name : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"screen_name","hash":{},"data":data}) : helper)))
    + "</p>  \n  </div>\n  <div class=\"tweet_content\">\n    <p class=\"tweet_text\">"
    + alias4(((helper = (helper = helpers.text || (depth0 != null ? depth0.text : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"text","hash":{},"data":data}) : helper)))
    + "</p>\n"
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.media : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "  </div>\n</div>\n";
},"useData":true});
})();