"""
Intrinsic functions, see:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
For more information.
"""

from attrs import frozen


@frozen
class IntrinsicFunction:
    function: str
    documentation: str
    full_name_prefix: str = "Fn::"
    short_form_prefix: str = "!"

    def short_form(self) -> str:
        return self.short_form_prefix + self.function

    def full_name(self) -> str:
        return self.full_name_prefix + self.function


# Hard coded temporarily (?)
INTRINSIC_FUNCTIONS = [
    IntrinsicFunction(
        function="Base64",
        documentation="The intrinsic function `Fn::Base64` returns the Base64 representation of the  \ninput string\\. This function is typically used to pass encoded data to Amazon  \nEC2 instances by way of the `UserData` property\\.",
    ),
    IntrinsicFunction(
        function="Cidr",
        documentation="The intrinsic function `Fn::Cidr` returns an array of CIDR address blocks\\. The  \nnumber of CIDR blocks returned is dependent on the `count` parameter\\.",
    ),
    IntrinsicFunction(
        function="FindInMap",
        documentation="The intrinsic function `Fn::FindInMap` returns the value corresponding to keys  \nin a two\\-level map that's declared in the `Mappings` section\\.",
    ),
    IntrinsicFunction(
        function="GetAtt",
        documentation="The `Fn::GetAtt` intrinsic function returns the value of an attribute from a  \nresource in the template\\. When the [`AWS::LanguageExtensions` transform](transform-aws-languageextensions.md)  \ntransform is used, you can use intrinsic functions as a parameter to  \n`Fn::GetAtt`\\. For more information about `GetAtt` return values for a  \nparticular resource, refer to the documentation for that resource in the  \n[Resource and property reference](aws-template-resource-type-ref.md)\\.",
    ),
    IntrinsicFunction(
        function="GetAZs",
        documentation="The intrinsic function `Fn::GetAZs` returns an array that lists Availability  \nZones for a specified region in alphabetical order\\. Because customers have  \naccess to different Availability Zones, the intrinsic function `Fn::GetAZs`  \nenables template authors to write templates that adapt to the calling user's  \naccess\\. That way you don't have to hard\\-code a full list of Availability Zones  \nfor a specified region\\.",
    ),
    IntrinsicFunction(
        function="ImportValue",
        documentation="The intrinsic function `Fn::ImportValue` returns the value of [an output exported](outputs-section-structure.md)  \nby another stack\\. You typically use this function to  \n[create cross\\-stack references](walkthrough-crossstackref.md)\\. In the following example template snippets,  \nStack A exports VPC security group values and Stack B imports them\\.",
    ),
    IntrinsicFunction(
        function="Join",
        documentation="The intrinsic function `Fn::Join` appends a set of values into a single value,  \nseparated by the specified delimiter\\. If a delimiter is the empty string, the  \nset of values are concatenated with no delimiter\\.",
    ),
    IntrinsicFunction(
        function="Select",
        documentation="The intrinsic function `Fn::Select` returns a single object from a list of  \nobjects by index\\.",
    ),
    IntrinsicFunction(
        function="Split",
        documentation="To split a string into a list of string values so that you can select an element  \nfrom the resulting string list, use the `Fn::Split` intrinsic function\\. Specify  \nthe location of splits with a delimiter, such as `,` \\(a comma\\)\\. After you  \nsplit a string, use the [`Fn::Select`](intrinsic-function-reference-select.md) function to pick a specific element\\.",
    ),
    IntrinsicFunction(
        function="Sub",
        documentation="The intrinsic function `Fn::Sub` substitutes variables in an input string with  \nvalues that you specify\\. In your templates, you can use this function to  \nconstruct commands or outputs that include values that aren't available until you  \ncreate or update a stack\\.",
    ),
    IntrinsicFunction(
        function="Transform",
        documentation="The intrinsic function `Fn::Transform` specifies a macro to perform custom  \nprocessing on part of a stack template\\. Macros enable you to perform custom  \nprocessing on templates, from simple actions like find\\-and\\-replace operations  \nto extensive transformations of entire templates\\. For more information, see  \n[Using AWS CloudFormation macros to perform custom processing on templates](template-macros.md)\\.",
    ),
    IntrinsicFunction(
        function="And",
        documentation="Returns `true` if all the specified conditions evaluate to true, or returns  \n`false` if any one of the conditions evaluates to false\\. `Fn::And` acts as  \nan AND operator\\. The minimum number of conditions that you can include is 2,  \nand the maximum is 10\\.",
    ),
    IntrinsicFunction(
        function="Equals",
        documentation="Compares if two values are equal\\. Returns `true` if the two values are  \nequal or `false` if they aren't\\.",
    ),
    IntrinsicFunction(
        function="If",
        documentation="For the `Fn::If` function, you only need to specify the condition name\\. The  \nfollowing snippet shows how to use `Fn::If` to conditionally specify a resource  \nproperty\\. If the `CreateLargeSize` condition is true, CloudFormation sets the  \nvolume size to `100`\\. If the condition is false, CloudFormation sets the volume  \nsize to `10`\\.",
    ),
    IntrinsicFunction(
        function="Not",
        documentation="Returns `true` for a condition that evaluates to `false` or returns `false`  \nfor a condition that evaluates to `true`\\. `Fn::Not` acts as a NOT operator\\.",
    ),
    IntrinsicFunction(
        function="Or",
        documentation="Returns `true` if any one of the specified conditions evaluate to true, or  \nreturns `false` if all the conditions evaluates to false\\. `Fn::Or` acts as an OR  \noperator\\. The minimum number of conditions that you can include is 2, and the maximum  \nis 10\\.",
    ),
    IntrinsicFunction(
        function="Ref",
        full_name_prefix="",
        documentation="The intrinsic function `Ref` returns the value of the specified *parameter* or  \n*resource*\\. When the [`AWS::LanguageExtensions` transform](transform-aws-languageextensions.md) transform is used, you  \ncan use intrinsic functions as a parameter to [`Ref`](#intrinsic-function-reference-ref) and [`Fn::GetAtt`](intrinsic-function-reference-getatt.md)\\. \n + When you specify a parameter's logical name, it returns the value of the parameter\\.\n + When you specify a resource's logical name, it returns a value that you can  \ntypically use to refer to that resource, such as a [physical ID](resources-section-structure.md)\\. \n + When you specify an intrinsic function, it returns the output of that function\\.",
    ),
]
