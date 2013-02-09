ample.bind('load', function(event) {
    $('#dataset-tree-box').attr('height', window.innerHeight - 16)
})
window.onresize = function(event) {
    $('#dataset-tree-box').attr('height', event.target.innerHeight - 16)
}

var rest = ample.restful('url', ample.restful.UPDATERS)
var edit = ample.restful('editor', ample.restful.UPDATERS, {headers:{'X-View-Name':'editor'}})
ample.rest = rest
ample.edit = edit
function prompt_or_cancel(message) {
    var value = prompt(message)
    if(_.isNull(value)) throw 'cancel'
    return value
}
function parent(node, name) {
    if(node.__proto__.localName == name) {
        return node
    }
    if(!node.parentNode) {
        throw 'Not existent parent "' + name + '"'
    }
    return parent(node.parentNode, name)
}

function deletenode(node, data){
    var selection = ample.rest.context.get(node);
    var update_root = _.after(selection.length, function(item) {
        rest(item.parentNode).with("GET")
    });
    _.map(selection, function(item) {
        item.setAttribute('open', false)
        if(item.attributes.url) {
            ample.ajax({
                data:data || null,
                url: item.attributes.url,
                type: "DELETE",
                complete: _.bind(update_root, {}, item)
            })
        }
    })
}
var dataset = {
    delete: function(menuitem) {
        deletenode(menuitem, null)
    },
    rebase: function(menuitem, copy){
        if (_.isUndefined(copy)){
            var copy = false
        }
        var selection = rest.context.get(menuitem);
        var update_root = _.after(selection.length, function(item) {
            rest(item.parentNode).with("GET")
        });
        _.map(selection, function(item) {
            $(item.parentNode.items).attr('open', false)
            try{
                var name = prompt_or_cancel('Enter datset new name')    
            }catch(err){
                if (err=='cancel'){
                    return
                }
            }
            
            if(item.attributes.url) {
                ample.ajax({
                    data:{name:name, copy:copy},
                    url: item.attributes.url,
                    type: "POST",
                    complete: _.bind(update_root, {}, item)
                })
            }
        })        
    }
}
var datasource = {
    create:function(menuitem, type){
        var selection = rest.context.get(menuitem);
        _.map(selection, function(item){
            $(item.parentNode.items).attr('open', false)
            ample
            .rest(item.children)
            .with("PUT", {type:type, name:function(){return prompt_or_cancel('Enter datasource name')}},
                function(){$(item.parentNode.items).attr('open', true)})
        })
    return true
    },
    delete: function(menuitem) {
        deletenode(menuitem, null)
    },
    deletetree: function(menuitem) {
        deletenode(menuitem, {subnodes:true})
    },
    change_type: function(menuitem, type){
        var selection = rest.context.get(menuitem);
        var update_root = _.after(selection.length, function(item) {
            rest(item.parentNode).with("GET")
        });
        _.map(selection, function(item) {
            $(item.parentNode.items).attr('open', false)
            if(item.attributes.url) {
                ample.ajax({
                    data:{typename:type},
                    url: item.attributes.url,
                    type: "POST",
                    complete: _.bind(update_root, {}, item)
                })
            }
        })
    }
}
function show_editor(treeitem){
    edit('#editor-box').using(treeitem).with('GET')
}
