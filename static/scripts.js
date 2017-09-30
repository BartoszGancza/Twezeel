// ajax loader gif
loader = "<img alt='loading' src='/static/ajax-loader.gif'/>";

$("#recent_prep").ready(function() {
    $("#recent").html(loader);
    $.getJSON(Flask.url_for("get_tweets"))
        .done(function(data, textStatus, jqXHR) {

            content_tweet = "";

            for (var index in data)
            {
                // data just contains pure html as per fetch by API call
                content_tweet += data[index];
            }

            $("#recent").html(content_tweet);
            })
        .fail(function(jqXHR, textStatus, errorThrown) {

            // log error to browser's console
            console.log(errorThrown.toString());
        });
});

$(document).ready(function() {

    $('[data-toggle="tooltip"]').tooltip({placement: "right"});

    // fades out the flashed message (log in, log out, etc.)
    if ($(".alert.alert-info"))
    {
        $(".alert.alert-info").delay(3000).fadeOut();
    }

    // fetches 10 mentions for the user and displays them in the tab
    $("#mentions_prep").click(function() {
        // shows the AJAX loader
        $("#mentions").html(loader);
        $.getJSON(Flask.url_for("get_mentions"))
            .done(function(data, textStatus, jqXHR) {

                content_mention = "";

                for (var index in data)
                {
                    // data just contains pure html as per fetch by API call
                    content_mention += data[index];
                }

                $("#mentions").html(content_mention);
                })
            .fail(function(jqXHR, textStatus, errorThrown) {

                // log error to browser's console
                console.log(errorThrown.toString());
            });
    });

    // fetches 20 direct messages from OTHER users and displays them in the proper tab
    $("#dm_prep").click(function() {
        $("#dm").html(loader);
        $.getJSON(Flask.url_for("get_dm"))
            .done(function(data, textStatus, jqXHR) {

                content_dm = "";
                userPrevious = "";

                for (var index in data)
                {
                    // put all the DM's from the same person into single frame instead of having each in a separate one
                    if (data[index].sender.screen_name == userPrevious)
                    {
                        content_dm += "<p>" + data[index].text + "</p>";
                    }
                    else
                    {
                        // 2 divs at the beginning look strange, but browser omits them in the first box and everything works as intended
                        content_dm += `</div></div><div id="opacity">
                            <div style="float: left">
                            <img src="` + data[index].sender.profile_image_url + `" style="border-radius: 10px; max-width: 35px; height: auto;">
                            <span style="vertical-align: center">
                            <a href="https://twitter.com/` + data[index].sender.screen_name + `" style="padding-left: 10px">@` + data[index].sender.screen_name + `</a> said:
                            </span>
                            </div>
                            <div style="padding-top: 25px">
                            <hr style="border-width: 1px; border-style: groove; width: 80%">
                            <p>` + data[index].text + `</p>`;
                    }

                    // used to check if same user at the next run of the loop
                    userPrevious = data[index].sender.screen_name;
                }

                $("#dm").html(content_dm);
                })
            .fail(function(jqXHR, textStatus, errorThrown) {

                // log error to browser's console
                console.log(errorThrown.toString());
            });
    });

    // fetches 30 newest followers for the user and displays them in the tab
    $("#followers").ready(function() {
        // shows the AJAX loader
        $("#followers").html(loader);
        $.getJSON(Flask.url_for("followers"))
            .done(function(data, textStatus, jqXHR) {

                content_followers = "<table class='followers_table'>";
                counter = 0;

                for (i = 0; i < 3; i++)
                {
                    content_followers += "<tr>";

                    for (j = 0; j < 10; j++)
                    {
                        content_followers += `<td><a data-toggle="tooltip" title="` + data[counter].name +
                        `" href="https://twitter.com/` + data[counter].screen_name +
                        `"><img alt="profile image" src="` + data[counter].profile_image_url + '"></a></td>';
                        counter += 1;
                    }

                    content_followers += "</tr>";
                }

                content_followers += "</table>";

                $("#followers").html(content_followers);
                $('[data-toggle="tooltip"]').tooltip({placement: "right"});
                })
            .fail(function(jqXHR, textStatus, errorThrown) {

                // log error to browser's console
                console.log(errorThrown.toString());
            });
    });

    /* Emoji picker thanks to/documentation at https://github.com/xLs51/Twemoji-Picker */
    $("#twemoji-picker").twemojiPicker({
      iconSize: '25px',
      height: '150px',
      width: '100%',
      category: ['smile', 'cherry-blossom', 'video-game', 'oncoming-automobile', 'symbols'],
      categorySize: '20px',
      pickerPosition: 'bottom',
      pickerHeight: '150px',
      pickerWidth: '100%'
    });

    $(".twemoji-textarea").keyup(function () {
        var max = 140;
        var len = $("#twemoji-picker").val().length;
        if (len > max)
        {
            $("#charNum").css("color", "red");
            var char = max - len;
            $("#charNum").text(char + "/140");
        }
        else
        {
            $("#charNum").css("color", "#c8c8c8");
            char = max - len;
            $("#charNum").text(char + "/140");
        }
    });
});