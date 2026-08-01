// Inlined so every page gets the same nav without a separate header.html
// fetch (browsers were caching the old "Contact Me" version on localhost).
(function () {
  const placeholder = document.getElementById("header-placeholder");
  if (!placeholder) return;

  placeholder.innerHTML = `<header id="header">
	<div class="inner">
		<a href="/" class="image avatar"><img src="/images/profile.jpg" alt="" /></a>
		<h1><strong>I am Irene Sha</strong>,  <br />
		a Mech Eng PhD Candidate at <br />
		Princeton University.</h1>
	</div>
	<nav class="header-nav">
		<ul>
			<li><a href="/"><i class="fas fa-home"></i><span>Home</span></a></li>
			<li><a href="/cad-portfolio/"><i class="fas fa-drafting-compass"></i><span>CAD Portfolio</span></a></li>
			<li><a href="/hobbies/"><i class="fas fa-heart"></i><span>Hobbies</span></a></li>
			<li><a href="/about/"><i class="fas fa-user"></i><span>About Me</span></a></li>
			<li><a href="https://www.linkedin.com/in/irene-sha/" class="icon brands fa-linkedin nav-icon-only" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><span class="label">LinkedIn</span></a></li>
		</ul>
	</nav>
</header>`;
})();
