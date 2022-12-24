import requests


class ResourceIndexSearch:
    def __init__(self, language="sparql", riformat="CSV", ri_endpoint="https://porter.lib.utk.edu/fedora/risearch"):
        self.risearch_endpoint = ri_endpoint
        self.valid_languages = ("itql", "sparql")
        self.valid_formats = ("CSV", "Simple", "Sparql", "TSV", "JSON")
        self.language = self.validate_language(language)
        self.format = self.validate_format(riformat)
        self.base_url = (
            f"{self.risearch_endpoint}?type=tuples"
            f"&lang={self.language}&format={self.format}"
        )

    @staticmethod
    def escape_query(query):
        return (
            query.replace("*", "%2A")
                .replace(" ", "%20")
                .replace("<", "%3C")
                .replace(":", "%3A")
                .replace(">", "%3E")
                .replace("#", "%23")
                .replace("\n", "")
                .replace("?", "%3F")
                .replace("{", "%7B")
                .replace("}", "%7D")
                .replace("/", "%2F")
        )

    def validate_language(self, language):
        if language in self.valid_languages:
            return language
        else:
            raise Exception(
                f"Supplied language is not valid: {language}. Must be one of {self.valid_languages}."
            )

    def validate_format(self, user_format):
        if user_format in self.valid_formats:
            return user_format
        else:
            raise Exception(
                f"Supplied format is not valid: {user_format}. Must be one of {self.valid_formats}."
            )

    @staticmethod
    def __clean_csv_results(split_results, uri_prefix):
        results = []
        for result in split_results:
            if result.startswith(uri_prefix):
                new_result = result.split(",")
                results.append(
                    (new_result[0].replace(uri_prefix, ""), int(new_result[1]))
                )
        return sorted(results, key=lambda x: x[1])

    def get_files(self, pid):
        if self.language != "sparql":
            raise Exception(
                f"You must use sparql as the language for this method.  You used {self.language}."
            )
        sparql_query = self.escape_query(
            f"SELECT $files FROM <#ri> WHERE {{ <info:fedora/{pid}> "
            f"<info:fedora/fedora-system:def/view#disseminates> $files . }}"
        )
        results = requests.get(f"{self.base_url}&query={sparql_query}").content.decode('utf-8').split('\n')
        return [result.split('/')[-1] for result in results if result.startswith('info')]

    def __request_pids(self, request):
        results = requests.get(f"{self.base_url}&query={request}").content.decode('utf-8').split('\n')
        return [result.split('/')[-1] for result in results if result.startswith('info')]

    def __request_json(self, request):
        return requests.get(f"{self.base_url}&query={request}").json()

    def get_images_no_parts(self, collection):
        members_of_collection_query = self.escape_query(
            f"""SELECT ?pid FROM <#ri> WHERE {{ ?pid <info:fedora/fedora-system:def/model#hasModel> <info:fedora/islandora:sp_large_image_cmodel> ; <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> <info:fedora/{collection}> . }}"""
        )
        members_of_collection_parts_query = self.escape_query(
            f"""SELECT ?pid FROM <#ri> WHERE {{ ?pid <info:fedora/fedora-system:def/model#hasModel> <info:fedora/islandora:sp_large_image_cmodel> ; <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> <info:fedora/{collection}> ; <info:fedora/fedora-system:def/relations-external#isConstituentOf> ?unknown. }}"""
        )
        members_of_collection = self.__request_pids(members_of_collection_query)
        members_of_collection_parts = self.__request_pids(members_of_collection_parts_query)
        members_of_collection_no_parts = [pid for pid in members_of_collection if pid not in members_of_collection_parts]
        return members_of_collection_no_parts

    def get_parent_collections(self, pid):
        query = self.escape_query(
            f"""SELECT ?parent FROM <#ri> WHERE {{<info:fedora/{pid}> <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> ?parent .}}"""
        )
        collections = self.__request_pids(query)
        return collections

    def get_members_types_and_collections(self, pid):
        query = self.escape_query(
            f"""SELECT ?pid ?work_type ?collection FROM <#ri> WHERE {{?pid <info:fedora/fedora-system:def/relations-external#isMemberOfCollection> <info:fedora/{pid}> ;<info:fedora/fedora-system:def/model#hasModel> ?work_type ;<info:fedora/fedora-system:def/relations-external#isMemberOfCollection> ?collection .}}"""
        )
        results = self.__request_json(query)
        return results

    def get_islandora_work_type(self, pid):
        query = self.escape_query(
            f"""SELECT ?work_type FROM <#ri> WHERE {{<info:fedora/{pid}> <info:fedora/fedora-system:def/model#hasModel> ?work_type .}}"""
        )
        results = requests.get(f"{self.base_url}&query={query}").content.decode('utf-8')
        return [result.strip() for result in results.split('\n') if "info:fedora/fedora-system:FedoraObject-3.0" not in result ][1]

    def get_pid_based_on_page_number(self, parent, page):
        query = self.escape_query(
            f"""SELECT ?pid FROM <#ri> WHERE {{  ?pid <http://islandora.ca/ontology/relsext#isPageOf> <info:fedora/{parent}> ; <http://islandora.ca/ontology/relsext#isPageNumber> "{page}" . }} """
        )
        results = requests.get(f"{self.base_url}&query={query}").content.decode('utf-8')
        return [result.strip().replace('info:fedora/', '') for result in results.split('\n') if "pid" not in result][0]

if __name__ == "__main__":
    pages_to_restrict = []
    pids_to_restrict = []
    with open('dec_22_zac.txt', 'r') as pages_to_find:
        for line in pages_to_find:
            seqmented_line = line.split('/')
            pid = seqmented_line[6].replace('#page', '').replace('%3A', ':')
            page = seqmented_line[7]
            pages_to_restrict.append((pid, page))
    for page in pages_to_restrict:
        pids_to_restrict.append(ResourceIndexSearch().get_pid_based_on_page_number(page[0], page[1]))
    with open('pages_to_restrict.txt', 'w') as output:
        output.write(f"{}")



