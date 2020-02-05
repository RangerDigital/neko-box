#!/usr/bin/env python3

import os
import timeago
import requests
import textwrap

from datetime import datetime

GH_API = "https://api.github.com"
ANILIST_API = "https://graphql.anilist.co"


GIST_ID = os.environ["INPUT_GIST_ID"]
GH_TOKEN = os.environ["INPUT_GH_TOKEN"]
ANILIST_USERNAME = os.environ["INPUT_ANILIST_USERNAME"]


def update_gist(description, content):
    params = {"scope": "gist"}
    headers = {"Authorization": "token {}".format(GH_TOKEN)}
    payload = {"description": description, "public": True, "files": {"Powered by Neko-Box!": {"content": content}}}

    response = requests.post(GH_API + "/gists/" + GIST_ID, headers=headers, params=params, json=payload)

    if response.status_code == 200 or response.status_code == 201:
        print("Done! The gist was successfully updated!")
    else:
        raise Exception("Error while updating Gist, check your token!")


def run_query(query, variables):
    response = requests.post(ANILIST_API, json={"query": query, "variables": variables})

    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception("AniList query failed, check the provided username!")


def main():
    # Get AniList user Id from username.
    query = '''
        query ($username: String) {
          User (name: $username) {
            id
          }
        }
    '''

    variables = {
        "username": ANILIST_USERNAME
    }

    user_id = run_query(query, variables)["User"]["id"]

    # Get latest AniList activity by user Id.
    query = '''
        query ($user_id: Int) {
          Activity (userId: $user_id, sort: ID_DESC) {
              ... on ListActivity {
                type
                createdAt
                replyCount
                likeCount
                status
                progress
                media {
                    title {
                        romaji
                    }
                }
            }
            ... on TextActivity {
                type
                createdAt
                replyCount
                likeCount
                text
                }
          }
        }
    '''

    variables = {
        "user_id": user_id
    }

    activity = run_query(query, variables)["Activity"]

    # Calculate time since the last activity.
    created_at = datetime.fromtimestamp(activity["createdAt"])
    time_ago = timeago.format(created_at, datetime.now())

    # Truncate and wrap long text.
    if activity["type"] == "TEXT":
        text = (activity["text"][:150] + "...") if len(activity["text"]) > 150 else activity["text"]
        content = textwrap.fill(text, width=58)

    # Create a media activity message.
    elif activity["type"] == "ANIME_LIST" or activity["type"] == "MANGA_LIST":
        line_break = "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔".center(42)
        progress = activity["progress"] if activity["progress"] else "all"
        status = "{} {} {} of...".format(ANILIST_USERNAME, activity["status"], progress)
        content = "{}\n{}\n{}".format(status, activity["media"]["title"]["romaji"].center(58), line_break)

    else:
        print("Latest activity type not supported! Exiting...")
        return

    post_stats = "📢 {} | 💖 {}".format(activity["replyCount"], activity["likeCount"])
    payload = content + "\n" + post_stats.center(58)

    update_gist("🎀 AniList Activity - {}...".format(time_ago), payload)


if __name__ == "__main__":
    main()
