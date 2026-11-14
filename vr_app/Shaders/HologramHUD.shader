Shader "Cardiastracont/HologramHUD"
{
    Properties
    {
        _MainTex ("Base Texture", 2D) = "white" {}
        _TintColor ("Hologram Tint Color", Color) = (0.1, 0.8, 1.0, 0.8)
        _ScanlineSpeed ("Scanline Speed", Float) = 4.0
        _ScanlineDensity ("Scanline Density", Float) = 60.0
        _FresnelPower ("Fresnel Rim Power", Float) = 2.0
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        LOD 100
        Blend SrcAlpha One
        ZWrite Off
        Cull Back

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
                float3 worldNormal : TEXCOORD1;
                float3 viewDir : TEXCOORD2;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _TintColor;
            float _ScanlineSpeed;
            float _ScanlineDensity;
            float _FresnelPower;

            v2f vert (appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);

                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.viewDir = WorldSpaceViewDir(v.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);

                fixed4 tex = tex2D(_MainTex, i.uv);
                
                // Holographic scanline oscillation
                float scanline = sin((i.uv.y * _ScanlineDensity) + (_Time.y * _ScanlineSpeed)) * 0.15 + 0.85;

                // Subtle edge fresnel glow
                float3 normal = normalize(i.worldNormal);
                float3 viewDir = normalize(i.viewDir);
                float fresnel = 1.0 - saturate(dot(normal, viewDir));
                fresnel = pow(fresnel, _FresnelPower);

                fixed4 col = tex * _TintColor * scanline;
                col.rgb += _TintColor.rgb * fresnel * 0.5;
                col.a *= (tex.a + fresnel * 0.3);

                return col;
            }
            ENDCG
        }
    }
}

