function isLoggedIn() {return false;}

document.getElementById("cartBtn").onclick = function() {
    if (isLoggedIn()) { alert("Redirecting to Cart...");} 
    else { alert("Please Log-in to access Cart"); return false;}
};
