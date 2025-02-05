(function () {
  console.log("ready!"); // sanity check
})();

const postElements = document.getElementsByClassName("entry");

for (var i = 0; i < postElements.length; i++) {
  postElements[i].addEventListener("click", function (event) {
    // Prevents the deletion if a button inside the post is clicked
    if (event.target.tagName.toLowerCase() === 'button') {
      // Call handleLike if a button is clicked and it's a like button
      if (event.target.classList.contains('like-button')) {
        const postId = event.target.dataset.postId;
        handleLike(postId);
      }
      return; // Stop further event processing
    }
    
    const postId = this.getElementsByTagName("h2")[0].getAttribute("id");
    const node = this;
    fetch(`/delete/${postId}`)
      .then(function (resp) {
        return resp.json();
      })
      .then(function (result) {
        if (result.status === 1) {
          node.parentNode.removeChild(node);
          console.log(result);
        }
        location.reload();
      })
      .catch(function (err) {
        console.log(err);
      });
  });
}

// Function to handle likes
function handleLike(postId) {
  fetch(`/like_post/${postId}`, { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'liked' || data.status === 'unliked') {
        const likesCountElement = document.getElementById(`like_count_${postId}`);
        likesCountElement.innerText = `${data.likes_count} Likes`; // Update like count from server response
      } else {
        alert(data.message); // Alert the message from the server if any
      }
    })
    .catch(error => console.error('Error liking the post:', error));
}
