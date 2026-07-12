// Minimal DOM + window stub to execute script.js top-to-bottom for sanity checks
global.window = {};
global.document = {};

// basic window properties used by the script
global.window.innerHeight = 800;
global.window.scrollY = 0;
global.window.pageYOffset = 0;
global.window.addEventListener = function(){ /* no-op */ };
global.window.requestAnimationFrame = function(cb){ return setTimeout(cb, 0); };
global.window.matchMedia = function(){ return { matches: false }; };

// minimal document API
global.document.querySelectorAll = function(){ return []; };
global.document.querySelector = function(selector){
	// return a minimal header stub used by onScroll
	if(selector === '.site-header'){
		return { classList: { add: function(){}, remove: function(){} }, style: {} };
	}
	return null;
};
global.document.getElementById = function(){ return null; };
global.document.createElement = function(){ return { className:'', appendChild:function(){}, style:{}, querySelector:function(){return null}, parentElement: null }; };
global.document.documentElement = { scrollHeight: 1200, _attrs: {}, setAttribute: function(k,v){ this._attrs[k]=v }, getAttribute: function(k){ return this._attrs[k] || null } };

// run the actual script
const path = require('path');
require(path.join(process.cwd(), 'script.js'));
console.log('script.js executed (stubbed DOM): OK');
