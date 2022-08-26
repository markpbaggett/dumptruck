import requests
import magic
import os
from urllib.parse import quote


class DataSetInjector:
    """Injects parts into a dataset."""
    def __init__(self, path_to_files, namespace, collection, parent):
        self.parent_directory = path_to_files
        self.namespace = namespace
        self.collection = collection
        self.parent = parent
        self.files_list = self.__crawl_path_to_files(path_to_files)

    @staticmethod
    def __crawl_path_to_files(path):
        for path, directory, file_objects in os.walk(path):
            return [file_object for file_object in file_objects]

    def ingest_parts(self, starting_sequence_number=1):
        for file_object in self.files_list:
            x = DataSetPart(
                path=f"{self.parent_directory}/{file_object}",
                namespace=self.namespace,
                label=file_object,
                collection=self.collection,
                state="A",
                parent=self.parent
            ).new(starting_sequence_number)
            print(f"Ingested {x}.")
            starting_sequence_number += 1


class FedoraObject:
    def __init__(
        self, fedora_url="http://localhost:8080", auth=("fedoraAdmin", "fedoraAdmin")
    ):
        self.fedora_url = fedora_url
        self.auth = auth

    def ingest(
        self,
        namespace,
        label,
        state="A",
    ):
        """Creates a new object in Fedora and returns a persistent identifier.
        Args:
            namespace (str): The namespace of the new persistent identifier.
            label (str): The label of the new digital object.
            state (str): The state of the new object. Must be "A" or "I".
        Returns:
            str: The persistent identifier of the new object.
        Examples:
            >>> FedoraObject().ingest("test", "My new digital object", "islandora:test")
            "test:1"
        """
        if state not in ("A", "I"):
            raise Exception(
                f"\nState specified for new digital object based on label: {label} is not valid."
                f"\nMust be 'A' or 'I'."
            )
        r = requests.post(
            f"{self.fedora_url}/fedora/objects/new?namespace={namespace}&label={label}&state={state}",
            auth=self.auth,
        )
        if r.status_code == 201:
            return r.content.decode("utf-8")
        else:
            raise Exception(
                f"Request to ingest object with label `{label}` failed with {r.status_code}."
            )

    def add_relationship(self, pid, subject, predicate, obj, is_literal="true"):
        """Add a relationship to a digital object.
        Args:
            pid (str): The persistent identifier to the object where you want to add the relationship.
            subject (str): The subject of the relationship.  This should refer to the pid (for external relationships)
            or the dsid (for internal relationships). For
            predicate (str): The predicate of the new relationship.
            obj (str): The object of the new relationship.  Can refer to a graph or a literal.
            is_literal (str): This defaults to "true" but can also be "false." It specifies whether the object is a graph or a literal.
        Returns:
            int: The status code of the post request.
        Examples:
            >>> FedoraObject().add_relationship(pid="test:6", subject="info:fedora/test:6",
            ... predicate="info:fedora/fedora-system:def/relations-external#isMemberOfCollection",
            ... obj="info:fedora/islandora:test", is_literal="false",)
            200
        """
        r = requests.post(
            f"{self.fedora_url}/fedora/objects/{pid}/relationships/new?subject={quote(subject, safe='')}"
            f"&predicate={quote(predicate, safe='')}&object={quote(obj, safe='')}&isLiteral={is_literal}",
            auth=self.auth,
        )
        if r.status_code == 200:
            return r.status_code
        else:
            raise Exception(
                f"Unable to add relationship on {pid} with subject={subject}, predicate={predicate}, and object={obj}, "
                f"and isLiteral as {is_literal}.  Returned {r.status_code}."
            )

    def change_versioning(self, pid, dsid, versionable="false"):
        """Change versioning of a datastream.
        Args:
             pid (str): The persistent identifier of the object to which the dsid belongs.
             dsid (str): The datastream id of the datastream you want to modify.
             versionable (str): Defaults to "false".  "false" or "true" on whether a datastream is versioned.
        Returns:
            int: The status code of the request.
        Examples:
            >>> FedoraObject().change_versioning("test:1", "RELS-EXT", "true")
            200
        """
        r = requests.put(
            f"{self.fedora_url}/fedora/objects/{pid}/datastreams/{dsid}?versionable={versionable}",
            auth=self.auth,
        )
        if r.status_code == 200:
            return r.status_code
        else:
            raise Exception(
                f"Unable to change versioning of the {dsid} datastream on {pid} to {versionable}.  Returned "
                f"{r.status_code}."
            )

    def add_managed_datastream(
        self,
        pid,
        dsid,
        file,
        versionable="true",
        datastream_state="A",
        checksum_type="DEFAULT",
        alt_label=""
    ):
        """Adds an internally managed datastream.
        This is not a one to one vesion of addDatastream.  It has been stripped down to fit one use case: internally
        managed content.  I'll add other methods if other use cases arise.
        Args:
            pid (str): The persistent identifier to the object when you want to add a file.
            dsid (str): The datastream id to assign your new file.
            file (str): The path to your file.
            versionable (str): Defaults to "true".  Specifies whether the datastream should have versioning ("true" or "false").
            datastream_state (str): Specify whether the datastream is active, inactive, or deleted.
            checksum_type (str): The checksum type to use.  Defaults to "DEFAULT". See API docs for options.
        Returns:
            int: The http status code of the request.
        Examples:
            >>> FedoraObject().add_managed_datastream("test:10", "AIP", "my_aip.7z")
            201
        """
        if checksum_type not in (
            "DEFAULT",
            "DISABLED",
            "MD5",
            "SHA-1",
            "SHA-256",
            "SHA-385",
            "SHA-512",
        ):
            raise Exception(
                f"\nInvalid checksum type specified for {pid} when adding the {dsid} datastream with {file}"
                f"content.\nMust be one of: DEFAULT, DISABLED, MD5, SHA-1, SHA-256, SHA-385, SHA-512."
            )
        if alt_label == "":
            alt_label = dsid
        mime = magic.Magic(mime=True)
        upload_file = {
            "file": (file, open(file, "rb"), mime.from_file(file), {"Expires": "0"})
        }
        r = requests.post(
            f"{self.fedora_url}/fedora/objects/{pid}/datastreams/{dsid}/?controlGroup=M&dsLabel={alt_label}&versionable="
            f"{versionable}&dsState={datastream_state}&checksumType={checksum_type}",
            auth=self.auth,
            files=upload_file,
        )
        if r.status_code == 201:
            return r.status_code
        else:
            raise Exception(
                f"\nFailed to create {dsid} datastream on {pid} with {file} as content. Fedora returned this"
                f"status code: {r.status_code}."
            )


class DataSetPart(FedoraObject):
    def __init__(
            self,
            path,
            namespace,
            label,
            collection,
            state,
            parent,
            fedora="http://localhost:8080",
            auth=("fedoraAdmin", "fedoraAdmin"),
    ):
        self.path = path
        self.namespace = namespace
        self.label = label
        self.collection = collection
        self.state = state
        self.parent = parent
        super().__init__(fedora, auth)

    def add_to_collection(self, pid):
        """Adds the object to a collection in Fedora."""
        return self.add_relationship(
            pid,
            f"info:fedora/{pid}",
            "info:fedora/fedora-system:def/relations-external#isMemberOfCollection",
            f"info:fedora/{self.collection}",
            is_literal="false",
        )

    def assign_binary_content_model(self, pid):
        """Assigns binary content model to digital object."""
        return self.add_relationship(
            pid,
            f"info:fedora/{pid}",
            "info:fedora/fedora-system:def/model#hasModel",
            "info:fedora/islandora:binaryObjectCModel",
            is_literal="false",
        )

    def __assign_a_parent_dataset(self, pid, parent):
        """Assigns a parent to the object"""
        return self.add_relationship(
            pid,
            f"info:fedora/{pid}",
            "info:fedora/fedora-system:def/relations-external#isConstituentOf",
            f"info:fedora/{parent}",
            is_literal="false",
        )

    def __add_sequence_number(self, pid, parent, sequence_number):
        """Assigns a sequence number to the object"""
        return self.add_relationship(
            pid,
            f"info:fedora/{pid}",
            f"http://islandora.ca/ontology/relsext#isSequenceNumberOf{parent.replace(':','_')}",
            str(sequence_number).rstrip(),
            is_literal="true",
        )

    def add_primary_object(self, pid):
        aip = ""
        aip = self.add_managed_datastream(pid, "OBJ", f"{self.path}", alt_label=self.path.split('/')[-1])
        if aip == "":
            raise Exception(
                f"\nFailed to create OBJ on {pid}. No file was found in {self.path}/AIP/."
            )
        return aip

    def add_policy(self, pid):
        # Make sure to set this first
        policy = self.add_managed_datastream(pid, "POLICY", "policies/POLICY.xml")
        if policy == "":
            raise Exception(
                f"\nFailed to create OBJ on {pid}. No file was found in {self.path}/AIP/."
            )
        return policy

    def add_thumbnail(self, pid):
        # Make sure to set this first
        thumbnail = self.add_managed_datastream(pid, "TN", "thumbnail/thumbnail.png")
        if thumbnail == "":
            raise Exception(
                f"\nFailed to create OBJ on {pid}. No file was found in {self.path}/AIP/."
            )
        return thumbnail

    def add_mods(self, pid):
        # Make sure to set this first
        mods = self.add_managed_datastream(pid, "MODS", "metadata/mods.xml")
        if mods == "":
            raise Exception(
                f"\nFailed to create OBJ on {pid}. No file was found in {self.path}/AIP/."
            )
        return mods

    def add_dc(self, pid):
        # Make sure to set this first
        mods = self.add_managed_datastream(pid, "DC", "metadata/dc.xml")
        if mods == "":
            raise Exception(
                f"\nFailed to create OBJ on {pid}. No file was found in {self.path}/AIP/."
            )
        return mods

    def new(self, sequence_number):
        pid = self.ingest(self.namespace, self.label, self.state)
        self.add_to_collection(pid)
        self.assign_binary_content_model(pid)
        self.change_versioning(pid, "RELS-EXT", "true")
        self.add_primary_object(pid)
        self.add_thumbnail(pid)
        self.add_policy(pid)
        self.add_mods(pid)
        self.__assign_a_parent_dataset(pid, self.parent)
        self.__add_sequence_number(pid, self.parent, sequence_number)
        return pid


if __name__ == "__main__":
    # x = DataSetPart(
    #     path="fedora/fedora.py",
    #     namespace="test",
    #     label="Test load of Fedora.py",
    #     collection="islandora:test",
    #     state="A",
    #     desriptive_metadata=""
    # ).new()
    DataSetInjector(
        path_to_files="/home/mark/for_kim",
        namespace="test",
        collection="islandora:test",
        parent="test:21"
    ).ingest_parts()
