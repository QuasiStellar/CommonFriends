# Create a new VK app https://vk.com/apps?act=manage
# Create `secret.py` file with APP_ID and TOKEN values from your app
from secret import APP_ID, TOKEN

import vk
import time
import sys
import networkx as nx

from bokeh.io import show, save
from bokeh.models import Range1d, Circle, MultiLine
from bokeh.plotting import figure
from bokeh.plotting import from_networkx

# Graph construction based on https://github.com/BorZzzenko/FriendsGraph


class VkData:
    APP_ID = APP_ID
    TOKEN = TOKEN
    VERSION = "5.103"


class User:
    def __init__(self, us_info):
        self.id = us_info["id"]
        self.first_name = us_info["first_name"]
        self.last_name = us_info["last_name"]

        if "is_closed" in us_info:
            self.is_closed = us_info["is_closed"]
        else:
            self.is_closed = True

        if "is_deactivated" in us_info:
            self.is_closed = True

        self.domain = us_info["domain"]

    def __str__(self):
        return "{0} {1}\n".format(self.first_name, self.last_name)


def get_friends(vk_api, user_id, fields="domain"):
    friends = vk_api.friends.get(user_id=user_id, fields=fields)

    lst = [User(fr) for fr in friends["items"]]

    # In vk API there is a limit on requests per second.
    # Therefore, we sleep
    time.sleep(0.005)

    return lst


def main():
    if len(sys.argv) > 1:
        _id = sys.argv[1]
    else:
        _id = input("Enter user ID or screen_name: ").lstrip()

    session = vk.AuthSession(access_token=VkData.TOKEN)
    vk_api = vk.API(session, v=VkData.VERSION)

    # If user enters screen_name, we need to get his ID
    _id = vk_api.users.get(user_ids=_id)[0]["id"]

    # Friends Graph is a dictionary
    # Key - friend, graph vertex
    # Value - list of mutual friends, adjacent vertices
    graph = {}

    # Get list of friends for entered ID
    friends = get_friends(vk_api, _id)

    node_attrs = {}
    for friend in friends:
        print('Processing', "\tid: ", friend.id,
              "\tName : ", friend.first_name, friend.last_name)

        # If the profile is not hidden
        if not friend.is_closed:
            # Get friends of friend
            all_friends = get_friends(vk_api, friend.id)

            # Find mutual friends
            mutual = []
            for i in all_friends:
                for j in friends:
                    if i.id == j.id:
                        mutual.append(j.id)

            # Add value in dictionary
            graph[friend.id] = mutual
        else:
            graph[friend.id] = []

        node_attrs[friend.id] = friend.first_name + ' ' + friend.last_name

    g = nx.from_dict_of_lists(graph)
    nx.set_node_attributes(g, node_attrs, "name")

    title = 'Friends Network'

    hover_tooltips = [("Name", "@name")]

    plot = figure(tooltips=hover_tooltips, width=1840, height=930,
                  tools="pan,wheel_zoom,save,reset", active_scroll='wheel_zoom',
                  x_range=Range1d(-18.4, 18.4), y_range=Range1d(-9.3, 9.3), title=title)

    network_graph = from_networkx(g, nx.spring_layout, scale=10, center=(0, 0))
    network_graph.node_renderer.glyph = Circle(size=5, fill_color='skyblue')
    network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.1, line_width=1)

    plot.renderers.append(network_graph)

    show(plot)
    save(plot, filename=f"{title}.html")


if __name__ == '__main__':
    main()
