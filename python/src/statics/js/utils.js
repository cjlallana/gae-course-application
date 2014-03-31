
/**
 * Prototype that capitalizes the first character of a string
 */
String.prototype.capitalize = function()
{
	return this.charAt(0).toUpperCase() + this.slice(1);
}

/**
 * Checks if a given string is an integer.
 * @param n String to check.
 * @returns boolean 
 */
function isInteger(n)
{
	return !isNaN(parseInt(n)) && (n == parseInt(n)) && isFinite(n);
}

/**
 * Checks if a given string is a number.
 * @param n String to check.
 * @returns boolean 
 */
function isNumber(n) 
{
	return !isNaN(parseFloat(n)) && isFinite(n);
}

/**
 * Goes back to the previous page
 */
function goBack(){
	window.history.back();
}

/**
 * Disables the enter key when hit in a document.
 */
function disableEnterKey(e)
{
	var key;     
	if (window.event)
		key = window.event.keyCode; //IE
	else
		key = e.which; //firefox     

	return (key != 13);
}

/**
 * Sets the selector index on the option that matches the string
 */
function setStringSelector(selector, string)
{		
	var options	= selector.options;
	
	for (var i = 0; i < selector.length; i++){
		if (options[i].value == string){
			selector.selectedIndex = i;
			break;
		}
		else
			selector.selectedIndex = -1;
	}
}