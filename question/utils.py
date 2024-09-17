from .documents import QuestionDocument, AnswerDocument, CommentDocument, TagDocument





def search_tags(query) : 
    
    search = TagDocument.search(index="tags").query(
                "multi_match",
                query=query,
                fields=['name', 'description'],
                type="best_fields",
                fuzziness='AUTO'
            )
    results = search.execute()
    return results